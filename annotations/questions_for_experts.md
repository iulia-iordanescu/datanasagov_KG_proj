# Questions for subject-matter experts

The questions I ask subject-matter experts, one per decision an expert's answer would settle, each written out whole, so that an expert who knows nothing of this project can read it cold in a minute or two: the question (a few sub-questions, only those whose answer I need and can't derive from another), every record, term, entity class or predicate it names introduced where it appears, with the short quote that matters, as many records as examples as the point needs (each quoted in full here, and shown on the page by the sentences that matter, with its ground truth triples), the definitions of the ground truth schema, the rows of the translation table and the rules of the annotation guidelines the expert needs (quoted), the options I see, as plain choices, and my current reading. That part is all the expert reads to answer; it never names a record by its pool position or id, only by its title, in quotes. The rest is my bookkeeping, which the page shows folded at the bottom, under *The answer to this question impacts:*: *My notes* (with, word for word, whatever was taken out of the expert's part: nothing is deleted), *Quoted for us* (the definitions, rows and rules only I need), the *Consequences* of each option, and *Affects*, where each question lists everything its answer may change: every record and classed triple, row, ground truth schema entry, rule and pipeline method, not only the example. The review page (`py helpers/review_page.py`) shows the open ones in its **Questions** view, most urgent first, each with a box for the expert's answer, which comes back with their other comments.

This file is the questions' one home: I write and change them here, and nowhere else. The page reads it in a strict format, and refuses to be made while a question isn't in it, while a quote isn't what its source says now (a record's title or notes, a ground truth triple, a definition, a row, a rule), or while *Affects* leaves out a ground truth triple or a row of a ground truth schema entry it names, naming the line. Only tuning records may appear: the page refuses a held-out record. A new doubt that one of these answers would settle goes into that question (a sub-question, and its records and classed triples under *Affects*), not into a question of its own; a question keeps its number for good, since comments are filed under it. The format, and how to add to a question: [helpers/review_page.md](../helpers/review_page.md), *The questions file*.

## Q1: Should SpatialRepresentation be a closed list?

- status: open
- priority: high
- question kind: schema entry
- in short: the ground truth schema's SpatialRepresentation, and rule 11 of *Writing a classed triple* in the annotation guidelines

### The question

How a dataset's data are laid out over the ground, its spatial representation, is so far written in each [record](../docs/terminology.md#1-records-and-their-text)'s own words. The records we have read write it as "5 minutes of swath data", "gridded Level-3 products", "spatially gridded (L3)", "These data are maps" and "gridded Level 2 product". We are not sure whether to keep those words, or to use a closed list, the same few values for every record of the catalog. We would like to know:

- (a) Which layouts occur in this catalog, beyond swath and gridded? For data not on a grid, the CF conventions list a single point, a time series at one place, a trajectory (e.g. an aircraft's or a ship's track), a vertical profile, a time series of profiles, and a trajectory of profiles (Eaton, Gregory, Drach, Taylor, Hankin, et al., *NetCDF Climate and Forecast (CF) Metadata Conventions*, version 1.13, 17 December 2025, chapter 9, *Discrete Sampling Geometries*, Table 9.1; https://cfconventions.org/, doi:10.5281/zenodo.17801666). Our guess at which occur, by what collects the data, is in the table below: please complete or correct it.

| What collects the data | Spatial representations we expect |
|---|---|
| a satellite | swath; gridded |
| an aircraft, or a ship | a track (a trajectory) |
| a ground station | a point; a time series at one place |
| an instrument that measures along the vertical (e.g. a balloon) | a vertical profile |
| others? | ? |

### Example record

- record id: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- pool position: 3
- title: Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005
- notes: This data set consists of weekly gridded Level-3 products of Aquarius L-band radiometer Sea Surface Salinity (SSS) retrievals from the Aquarius/Satélite de Aplicaciones Científicas (SAC-D) mission, developed collaboratively between the U.S. National Aeronautics and Space Administration (NASA) and Argentina's space agency, Comisión Nacional de Actividades Espaciales (CONAE).
- source text: Polar
- source text: gridded Level-3 products
- classed triple: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation)
- classed triple: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_COVERAGE "Polar" (SpatialExtent)

### Ground truth schema

- entity class SpatialRepresentation: a form data are laid out in: over the ground, typically along a satellite's path, as observed (swath), or on a fixed map grid (gridded); or as images, image cubes, spectra or maps, e.g. swath; map; raw near-IR spectral image cubes
- predicate HAS_SPATIAL_REPRESENTATION: lays out its data as
- entity class Grid: a fixed set of cells or points that data values are given on, e.g. ISEAG; pressure grid with 24 levels per decade
- predicate ON_GRID: its values are given on the cells or points of this Grid

### Options

#### Option 1: Keep each record's own words

Each record keeps its own words for its layout, as written: "swath", "spatially gridded", "map", "gridded".

#### Option 2: A closed list

A short list of layouts (swath, gridded, and the others your answer to (a) names), and each record's layout is written as the value of the list its words mean, in place of its own words: "spatially gridded" becomes "gridded".

### My current reading

Undecided, leaning towards option 2, a closed list, if your answer to (a) gives a list that covers the catalog. Until then, we keep each record's own words (option 1). The example writes its layout twice, "Polar-Gridded" in its title and "gridded" in its notes; we wrote it once, as "gridded", and wrote "Polar" as the area the data cover, a fact of its own: its data cover only the polar regions.

### My notes

Checked against sources on 2026-10-30: "Polar-Gridded" (record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005") is gridded on EASE-Grid 2.0 North and South, covering only latitudes poleward of 50 degrees (NSIDC user guide, https://nsidc.org/sites/default/files/aq3_sss-v005-userguide_0.pdf); "1,200 by 1,200 km" is one tile of the MODIS sinusoidal grid, the ground each file covers ("Each tile has fixed Earth-locations covering an area of approximately 1200 x 1200 km", https://landweb.modaps.eosdis.nasa.gov/help/prod_format); no source calls "Global 1km SIN Grid" the grid's name (MODLAND: "Sinusoidal Tile Grid", https://modis-land.gsfc.nasa.gov/MODLAND_grid.html); NASA's metadata standard UMM-C has closed lists for granule spatial representation and tiling systems, but none of swath versus gridded layouts.

We have annotated the first six records of the pool, all [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070), and we have now also annotated the seventh. Of these seven, five state a spatial representation: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" ("5 minutes of swath data": "swath"), "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" ("Polar-Gridded", written as "gridded" since 2026-10-31), "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" ("spatially gridded (L3)": "spatially gridded"), "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" ("These data are maps": "map") and "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" ("gridded Level 2 product": "gridded"). The example is the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005"; all five, with their classed triples, are listed under Affects.

Until the questions are answered, the ground truth keeps each record's own words: the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" keeps "spatially gridded" as written (rule 11 of *Writing a classed triple*, and its rule 19: "A qualifier stays in the instance, as written, if it is any other kind"). The record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" states no area, so its ground truth has none. Changed on 2026-10-31: it now has the area "Polar", see below.

Pending facts, for the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (4c64f3ed, in the ground truth now without them):

- pending fact: its fact 14, "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) BINNED_INTO "SIN Grid" or "Global 1km SIN Grid" (Grid), left out for now; added if the answer to (c) says a record's grid is a fact of its own (and which wording).

Pending facts, for the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (d5477563, in the ground truth now without them; decided 2026-10-25, for us to confirm; settled on 2026-10-31, below, *Decided on 2026-10-31 from the sources above (research G3)*: the grid is now the ground truth triple BINNED_INTO "SIN Grid", and the tile's size stays left out):

- pending fact: its fact 9, "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) BINNED_INTO "SIN Grid" or "Global 1km SIN Grid" (Grid), left out for now, as for the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid".
- pending fact: the grid's size, from "in a 1,200 by 1,200 km grid": "1,200 by 1,200 km" (Value), on the grid or on the dataset, with a predicate to coin; added with the grid if the answer to (c) says so.

The record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" also has "MOD11_L2" (Dataset) HAS_SPATIAL_REPRESENTATION "swath" (SpatialRepresentation), from "swath product": the layout of the input it is computed from, in the record's own word.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) now holds the old (a) and (d); their (b) the old (b) and the polar part of the old (c); their (c) the rest of the old (c). The answers' letters in the notes above follow the new lettering: (c) is still whether a record's grid is a fact of its own.

The question's opening, as it was: How a dataset's data are laid out over the ground is, so far, written in each record's own words: "swath", "Polar-Gridded", "spatially gridded", "map", "gridded". We are not sure whether to keep those words, or to use a closed list of values instead, the same few words for every record of the catalog. To decide, we need to know:

- (a) Is the spatial representation, for the records of this catalog, a closed set of values? Beyond swath and gridded, which layouts occur? The CF conventions name the layouts of data that are not on a grid, their discrete sampling geometries: a single point, a time series at one place, a trajectory (e.g. an aircraft's or a ship's track), a vertical profile, a time series of profiles, and a trajectory of profiles (Eaton, Gregory, Drach, Taylor, Hankin, et al., *NetCDF Climate and Forecast (CF) Metadata Conventions*, version 1.13, 17 December 2025, chapter 9, *Discrete Sampling Geometries*, Table 9.1; https://cfconventions.org/, doi:10.5281/zenodo.17801666). Which of these occur in this catalog, and are there others?
- (b) Is a Planetary Data System "map" product gridded? For example, the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "These data are maps of fast neutron residual count rates".
- (c) Is "Polar-Gridded" (in the example below) gridded, on a polar grid? That is, would it be the value gridded, plus a separate fact about which grid? The same for the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid", whose title ends in "Global 1km SIN Grid", the MODIS sinusoidal grid (checked, see below): should a record's grid be a fact of its own, written with the predicate BINNED_INTO and a Grid, as the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" already has: "pixels" (Dataset) BINNED_INTO "integerized sinusoidal area grid (ISEAG)" (Grid)? And does a polar grid say anything about the area the data cover: do "Polar-Gridded" data cover only the polar regions, or the whole Earth, laid out on a grid drawn around a pole? The example states no area, so we wrote none for it. The record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" ends in the same "Global 1km SIN Grid", and its notes add "with 1 kilometer (km) spatial resolution in a 1,200 by 1,200 km grid". Our reading, not checked against a source: "1,200 by 1,200 km" is the size of one tile of that grid. Is it, and should that size be a fact of its own, about the grid, or about how much ground each of the dataset's files covers?
- (d) What kinds of thing collect the data of this catalog, and for each kind, which spatial representations occur? Our guess is below: please complete or correct it.

The question's context, as it was: The records we have read so far write a layout in these words: "5 minutes of swath data" (written down as "swath"), "Polar-Gridded", "spatially gridded (L3)" (written down as "spatially gridded"), "These data are maps" ("map") and "gridded Level 2 product" ("gridded"). The example below writes its layout in two ways, "Polar-Gridded" in its title and "gridded" in its notes.

Checked on 2026-10-25: "SIN Grid" is the MODIS sinusoidal grid, and "Global 1km SIN Grid" is the usual end of the titles of the MODIS products made on it. Corrected on 2026-10-30: no source calls "Global 1km SIN Grid" the grid's name, and the sources treat "Global" as the product's worldwide coverage (NASA LAADS DAAC on the MODIS tiles: "Each tile has fixed Earth-locations covering an area of approximately 1200 x 1200 km (10 x 10 degrees at the equator)"; MODLAND calls the grid the "Sinusoidal Tile Grid" (https://modis-land.gsfc.nasa.gov/MODLAND_grid.html), and NASA CMR names its tiling system "MODIS Tile SIN"; CMR gives these products global spatial coverage; 8 of the catalog's 384 "SIN Grid" titles have no "Global"), so both MODIS sinusoidal-grid records now have the ground truth triple HAS_SPATIAL_COVERAGE "Global" (rule 19). Kept from 2026-10-25: "Global" was read as naming the grid's worldwide tiling (NASA LAADS, the MCD19A2 product page, https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MCD19A2; NASA MODAPS, MCD19A2N, https://modaps.modaps.eosdis.nasa.gov/services/about/products/c61-nrt/MCD19A2N.html). Whether that grid is a fact of its own is still question (c).

Option 1, as it was: Each record keeps its own words for its layout, as written (rule 11 of *Writing a classed triple*): "swath", "Polar-Gridded", "spatially gridded", "map", "gridded". Option 2 named "the others your answers to (a) and (d) name". My current reading, as it was: Undecided, leaning towards option 2, a closed list, if the answers to (a) and (d) give a list that covers the catalog. Until then, the ground truth keeps each record's own words (option 1).

Decided on 2026-10-31: "Polar-Gridded" is gridded data that cover only the polar regions. NSIDC's user guide for this product (https://nsidc.org/sites/default/files/aq3_sss-v005-userguide_0.pdf): "SSS retrievals at latitudes greater than 50 degrees in both hemispheres are averaged and gridded into a weekly product", on EASE-Grid 2.0 North and South. So the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" now has "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation), from its notes' "gridded Level-3 products", and "Polar", taken out of the title's "Polar-Gridded" as the area the data cover, a ground truth triple of its own by rule 19, as "Global" was: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_COVERAGE "Polar" (SpatialExtent). Before, it had "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_REPRESENTATION "Polar-Gridded" (SpatialRepresentation), and no area.

Checked on 2026-10-30, as above: "1,200 by 1,200 km" is the size of one tile of the MODIS sinusoidal grid, the ground each file covers (NASA LAADS DAAC, https://landweb.modaps.eosdis.nasa.gov/help/prod_format: "Each tile has fixed Earth-locations covering an area of approximately 1200 x 1200 km (10 x 10 degrees at the equator)"; the catalog's sibling records MOD11B1, MOD11B2 and MOD11B3 say "in a 1,200 by 1,200 kilometer (km) tile"). So the expert's (c) now asks only whether that size is worth a fact of its own.

Taken out of the expert's view on 2026-10-31, as a question we can settle from sources; kept here word for word. The opening listed "Polar-Gridded" where it now lists "gridded Level-3 products". The example showed the source texts "Polar-Gridded" and "weekly gridded Level-3 products", and the classed triple "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_REPRESENTATION "Polar-Gridded" (SpatialRepresentation). The (c) ended: "And is "a 1,200 by 1,200 km grid" (the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006") the size of one tile of that grid, and worth a fact of its own?"

- (b) Are "Polar-Gridded" (the example below) and a Planetary Data System "map" (the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0": "These data are maps of fast neutron residual count rates") both gridded? And do "Polar-Gridded" data cover only the polar regions, or the whole Earth on a grid drawn around a pole? The example states no area, so we wrote none.

Option 1, as it was: Each record keeps its own words for its layout, as written: "swath", "Polar-Gridded", "spatially gridded", "map", "gridded". My current reading, as it was: Undecided, leaning towards option 2, a closed list, if your answer to (a) gives a list that covers the catalog. Until then, we keep each record's own words (option 1). The example writes its layout twice, "Polar-Gridded" in its title and "gridded" in its notes; we wrote it once, with "Polar-Gridded", the wording that says more. Option 1's consequences said: "One layout is written in different words in different records ("gridded", "spatially gridded", and perhaps "Polar-Gridded" and "map"), so a search of the knowledge graph for gridded data has to know every wording." Option 2's said: "The ground truth triples listed under Affects are checked again, and some object instances change ("spatially gridded"; "map" and "Polar-Gridded", depending on the answers to (b) and (c))." and "A record's own word for its layout ("Polar-Gridded") is no longer in that triple; what it adds to the value (a polar grid) is kept only if it is a fact of its own (question (c))."

Taken out of the expert's view on 2026-10-31, as settled by me; kept here word for word: "(c) Should the grid itself be a fact of its own? Some titles name it, e.g. "Global 1km SIN Grid" (the MODIS sinusoidal grid) in the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid". One record already has one: "pixels" (Dataset) BINNED_INTO "integerized sinusoidal area grid (ISEAG)" (Grid), in the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0". And is the size of one tile of that grid, the ground each file covers, worth a fact of its own ("a 1,200 by 1,200 km grid", in the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006")?" Decided on 2026-10-31 from the sources above (research G3): the grid is a fact of its own, as "pixels" (Dataset) BINNED_INTO "integerized sinusoidal area grid (ISEAG)" (Grid) already was, with the wording "SIN Grid", the grid's own name (rule 19 already takes "Global" and "1km" out of the title's "Global 1km SIN Grid"): "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) BINNED_INTO "SIN Grid" (Grid) and "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) BINNED_INTO "SIN Grid" (Grid), each with the source text "SIN Grid" (rule 17, *A title's facts*). The pending facts above are now these two; the third, the tile's size "1,200 by 1,200 km", stays left out: that it is the ground each file covers comes from NASA LAADS, not from the record (rule 1 of *What counts as a fact*), and the ground truth schema has no predicate for the ground each file covers (a twin of HAS_GRANULE_DURATION; docs/improvements.md, *Missing twin predicates in the ground truth schema*).

Taken out of the expert's view on 2026-10-31, as settled from sources (the research of 2026-10-31); kept here word for word: "- (b) Is a Planetary Data System "map" gridded? For example, the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "These data are maps of fast neutron residual count rates"." Option 2's consequences said "("spatially gridded"; "map", depending on the answer to (b))".

Checked on 2026-10-31, for the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0": its map is on a grid. The archive's label holds a TABLE of 114 rows, one per cell, and no MAP_PROJECTION object (https://sbnarchive.psi.edu/pds3/dawn/grand/DWNVGRD_2/DATA/FAST_NEUTRON/GRD_FAST_NEUTRON_RESIDUAL_MAP.LBL); its catalog file says "Each pixel spans [covers] a separate and unique portion of Vesta's surface, and together, the pixels provide full global coverage" and "All of the maps use rectangular pixels" (https://sbnarchive.psi.edu/pds3/dawn/grand/DWNVGRD_2/CATALOG/GRAND_VESTA_FAST_NEUTRON_RES_MAP_DS.CAT). My count of the table: latitude bands of 20 degrees, each split into cells 18 to 45 degrees wide, and a cap at each pole (a quasi-equal-area grid). That is "on a fixed map grid (gridded)" in SpatialRepresentation's definition (my reading that the definition fits). It is not established for every Planetary Data System map: the PDS3 data dictionary's MAP_PROJECTION_TYPE values are projections of images, which this data set doesn't use. Nothing changes now: under option 1 the ground truth keeps the record's word "map" (rule 11 of *Writing a classed triple*); under option 2 its value would be "gridded". The record names no grid, so no Grid is written (rule 1 of *What counts as a fact*); the grid's cells are for docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080).

Re-checked on 2026-10-31: the NSIDC quote for "Polar-Gridded" above ("SSS retrievals at latitudes greater than 50 degrees in both hemispheres are averaged and gridded into a weekly product") is in section 3.2 of the user guide, *Derivation Techniques and Algorithms*; the data cover latitudes poleward of 50 degrees on EASE-Grid 2.0 North and South (NSIDC's landing page, https://nsidc.org/data/aq3_sss/versions/5), which are for 080's enrichment, since the record states no latitudes.

Checked on 2026-10-31, for the expert's (a) (the research of 2026-10-31 on NASA's metadata): NASA's metadata standard UMM-C has no list of layouts, but its resolution kinds imply one. Each product's horizontal resolution is filed under one of Point, Gridded, NonGridded, Varies and Generic, the last "where it is not known if a data product is gridded or not" (UMM-C schema, `HorizontalDataResolution`). Providers fill it inconsistently: the swath product MYD10_L2 (Version 61) is filed with a gridded resolution of 500 m (https://cmr.earthdata.nasa.gov/search/concepts/C3090964320-NSIDC_CPRD.umm_json). So it is no closed list to copy. If option 2 is chosen, its top level could be point, gridded and non-gridded, with swath and profile under non-gridded and CF 1.13's discrete sampling geometries for the rest (my reading). UMM-C's GranuleSpatialRepresentation is no layout either: the swath MYD10_L2 and the gridded MOD11A1 are both GEODETIC. The count of layouts over the induction candidates is still to make.

### Quoted for us

- Writing a classed triple, rule 11: Subject instance and object instance: the record's own words, as written. Don't paraphrase them, and don't expand an abbreviation the record leaves unexpanded. Exceptions: What counts as a fact, rules 5, 9 and 10 (opinion words, words that only say how another fact holds, and words true only as of writing, are left out); and rules 19, 20, 22, 23 and 24 below (rule 20: parentheses that hold the code of something else are not part of the instance; rule 24: the words for a processing step's input and method are not part of another instance).
- Writing a classed triple, rule 16: Each fact once, even if the record states it twice or in other words. Rule 23 says which wording to keep. Suppose: a record says "This dataset provides daily snow cover", and later "snow cover is given each day". Then: the two sentences state one fact, so one ground truth triple: the record's dataset HAS_TEMPORAL_RESOLUTION "daily", the wording the record gives first (rule 23).
- Writing a classed triple, rule 19: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 19: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.
- Writing a classed triple, rule 22: A list: one ground truth triple per item.
- Writing a classed triple, rule 23: One thing, one wording, within a record.

### Consequences

#### Option 1: Keep each record's own words

- Nothing changes: not the annotation guidelines, not the copy of the rules the [model](../docs/terminology.md#8-the-pipeline) follows when it extracts (`common/common_prompts/extraction_rules.txt`), and not the ground truth triples listed under Affects.
- One layout is written in different words in different records ("gridded", "spatially gridded", and perhaps "map"), so a search of the knowledge graph for gridded data has to know every wording.

#### Option 2: A closed list

- A new exception to rule 11 of *Writing a classed triple*, like rules 19, 22 and 23 (quoted above): written in the annotation guidelines and in the copy of the rules the model follows, which both change.
- The ground truth triples listed under Affects are checked again, and some object instances change ("spatially gridded"; "map", which is on a grid of fixed cells: see My notes).
- The list has to cover the catalog: a record whose layout isn't on it has no value to use (question (a)).
- A record's own words for its layout ("spatially gridded") are no longer in that triple.
- Every record names a layout the same way, so a search of the knowledge graph for gridded data needs one value.

### Affects

- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 21: 264a9b23-9a86-46a7-ab61-9661230ea667
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_SPATIAL_REPRESENTATION "swath" (SpatialRepresentation)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_COVERAGE "Polar" (SpatialExtent)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_REPRESENTATION "spatially gridded" (SpatialRepresentation)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) HAS_SPATIAL_REPRESENTATION "map" (SpatialRepresentation)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation)
- classed triple of the record at pool position 7: "MOD11_L2" (Dataset) HAS_SPATIAL_REPRESENTATION "swath" (SpatialRepresentation)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) ON_GRID "SIN Grid" (Grid)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) ON_GRID "SIN Grid" (Grid)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_SPATIAL_REPRESENTATION "solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data" (SpatialRepresentation)
- classed triple of the record at pool position 21: "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (Dataset) HAS_SPATIAL_REPRESENTATION "raw near-IR spectral image cubes" (SpatialRepresentation)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_SPATIAL_REPRESENTATION "zonal" (SpatialRepresentation)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_SPATIAL_REPRESENTATION "geographical mapping" (SpatialRepresentation)
- ground truth schema entry: entity class SpatialRepresentation
- ground truth schema entry: predicate HAS_SPATIAL_REPRESENTATION
- rule: Writing a classed triple, rule 11
- rule: Writing a classed triple, rule 16
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which a closed list would change

## Q2: Mission or Spacecraft, when a mission and its spacecraft are written with the same words?

- status: open
- priority: high
- question kind: schema entry
- in short: the ground truth schema's Mission and Spacecraft, and FROM_MISSION and FROM_SPACECRAFT

### The question

Many records say where their data came from with one word that can mean a mission or the spacecraft that flew it, such as "DAWN", "Aqua", "Terra" or "Rosetta". Our schema has an entity class for each, Mission and Spacecraft, and a predicate for each: a dataset is FROM_MISSION a Mission, or FROM_SPACECRAFT a Spacecraft (all four defined below). When a record writes only such a word, we have to pick one of the two. We would like to know:

- (a) When a record says only "DAWN", "Aqua" or "Terra", with no "mission" or "satellite" next to it, would someone in your field read it as the spacecraft, the mission, or both at once?

### Context

NASA's own lists call Aqua "a NASA Earth Science satellite mission", one entry for both the mission and the spacecraft, so they don't settle the question for us. NASA's metadata standard for Earth science collections (UMM-C, in NASA's Common Metadata Repository) keeps a collection's platforms apart from its projects (its missions, campaigns and programs), and puts the same word in both: the MOD11A1 land surface temperature product lists "Terra" as its platform and as a project, and the MCD19A2 aerosol product lists "Terra" and "Aqua" as both.

### Example record

- record id: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- pool position: 1
- title: ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0
- notes: This is a Rosetta Radio Science data set, collected during the COMET ESCORT 4 phase 2015-10-22 to 2015-12-31. It is a Global Gravity measurement at the comet 67P and covers the time 2015-11-01T19:58:35.000 to 2015-11-02T04:59:27.000.
- source text: This is a Rosetta Radio Science data set
- source text: ROSETTA-ORBITER
- classed triple: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission)
- classed triple: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_PLATFORM "ROSETTA-ORBITER" (Platform)

### Ground truth schema

- entity class Mission: a named effort to collect data, from space, from the air, on water or on the ground, e.g. Rosetta; BARREL
- entity class Platform: a craft or station that carries Instruments, in space, in the air, on water or on the ground: a spacecraft, an aircraft, a balloon, a ship or a ground station, e.g. Aqua; Voyager 1
- predicate FROM_MISSION: was collected during this Mission
- predicate FROM_PLATFORM: was collected from this Platform

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or abbreviation stands for.

### Options

#### Option 1: Spacecraft where the words name the craft, Mission where they name the mission

What we do now: Spacecraft where the record's words name the craft that carries the instrument ("MODIS/Aqua", "on board the Aqua satellite", the first word of a Planetary Data System title); Mission where they name the mission ("a Rosetta Radio Science data set", "the … mission").

#### Option 2: Always Mission

Every such word is a Mission, whether the record names the craft or the mission.

#### Option 3: Both, a Mission and a Spacecraft

Every such word gives two facts, one with a Mission and one with a Spacecraft, in the same words.

#### Option 4: A rule by where the record comes from

A rule for each part of the catalog: for example, in a Planetary Data System title, such as "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0", the first word is the spacecraft that carried the instrument (what the Planetary Data System calls the instrument host); in "MODIS/Aqua", the word after the instrument is the spacecraft.

### My current reading

Option 1, because it follows the record's own words and adds nothing the record doesn't state. Each title pattern we know of holds for one family of titles only, not across the catalog, so we read such patterns as clues, not as a rule.

### My notes

Checked against sources on 2026-10-30, for the Planetary Data System records only: each such title is the data set's PDS3 DATA_SET_NAME, whose first component is the instrument host, a spacecraft for these records (PDS3 Standards Reference, chapter 6, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf); the archive names the mission separately (Rosetta: "INTERNATIONAL ROSETTA MISSION"; Stardust: "NEXT"). Limits: a host can also be Earth-based ("EAR"), a lander or a rover. Titles of Earth science records ("MODIS/Aqua …") were not researched. Researched on 2026-10-31: see below.

Of the [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) we have annotated so far, six name a mission or a spacecraft: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0", "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061", "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005", "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" and "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (the last is in the ground truth now); all their classed triples that the answer may change are listed under Affects. The example is the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0".

Checked on 2026-10-26 by fetching the pages: NASA's mission pages have two views, the *A to Z List* (https://www.nasa.gov/a-to-z-of-nasa-missions/, 664 entries; the reference list docs/improvements.md plans for missions, *Linking subject instances and object instances to reference lists*) and *Science Missions* (https://science.nasa.gov/science-missions/, about 450 entries, each with a one-line description, e.g. "Aqua is a NASA Earth Science satellite mission that is collecting data about the Earth's water cycle."). The A to Z List has entries "Aqua", "Terra", "Dawn", "Aquarius", "Stardust / Stardust NExT" and "Rosetta-Philae" (no plain "Rosetta"). Each is one entry for the mission and its spacecraft together, so neither view settles this question; the choice above still has to be made from the record's words.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. Sub-questions (b) and (d) below became the expert's (b); (c) and the rest of (b) we settle ourselves, from a source or once (a) and (b) are answered:

- (b) In a Planetary Data System data set title, such as "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" or "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0", is the first word the spacecraft that carried the instrument? Our reading, not checked against a source: these titles start with the spacecraft, which the Planetary Data System calls the instrument host. The record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" starts with "STARDUST", and its notes name the mission with other words, "the Stardust-NExT mission"; there we wrote both: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) FROM_SPACECRAFT "STARDUST" (Spacecraft), and "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) FROM_MISSION "Stardust-NExT" (Mission). The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" starts with "ROSETTA-ORBITER", and its notes say "acquired by the OSIRIS Narrow Angle Camera on the Rosetta spacecraft"; we read the two as one spacecraft and wrote "ROSETTA-ORBITER", the wording that says more (rule 23): "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) FROM_SPACECRAFT "ROSETTA-ORBITER" (Spacecraft) and "OSIRIS Narrow Angle Camera" (Instrument) ABOARD "ROSETTA-ORBITER" (Spacecraft). Is the orbiter the same as "the Rosetta spacecraft" there?
- (c) "Aquarius/Satélite de Aplicaciones Científicas (SAC-D) mission" (in the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005"): our reading, not checked against a source, is that Aquarius was an instrument carried on the SAC-D spacecraft, and Aquarius/SAC-D the mission. Is that right, and if so, should the record's "Aquarius L-band radiometer" be the only Instrument here, with no Spacecraft named?
- (d) Is there a rule that holds for this whole catalog, e.g. "a word that is only a mission's word is a Mission; a word written before an instrument (MODIS/Aqua) is a Spacecraft"?

The question's context, as it was: The example below has both. So far we have used Mission where the record writes the word "mission" or a mission's data set ("a Rosetta Radio Science data set", "the Aquarius/… (SAC-D) mission"), and Spacecraft where the word names the craft that carries the instrument ("MODIS/Aqua", "on board the Aqua satellite", "DAWN" in the title, "ROSETTA-ORBITER").

For the example, we wrote "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission), from "a Rosetta Radio Science data set", and "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_SPACECRAFT "ROSETTA-ORBITER" (Spacecraft), from its title. For the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0", we wrote only "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) FROM_SPACECRAFT "DAWN" (Spacecraft), from its title, although DAWN is also the name of the mission.

Checked on 2026-10-31, from sources found on 2026-10-30: the question that ends the old (b) above, "Is the orbiter the same as "the Rosetta spacecraft" there?", is answered by the archive's own documents. Rosetta's archive conventions give the instrument host, the first word of each title, only two values, "ROSETTA-ORBITER, ROSETTA-LANDER" (ESA, *ROSETTA Archive Conventions*, RO-EST-TN-3372, issue 10 rev. 1, section 3.2.2, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/DOCUMENT/ESA_DOC/RO_EST_TN_3372.PDF), and the OSINAC data set's title starts with "ROSETTA-ORBITER" (its catalog file, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/OSINAC/RO-C-OSINAC-4-ESC3-67P-M20-INFLDSTR-V1.0/CATALOG/DATASET.CAT). So "the Rosetta spacecraft" there is the orbiter (my reading of these labels), as the ground truth has it; no ground truth triple changes.

Taken out of the expert's view on 2026-10-31, as settled (no rule holds for the whole catalog, decided as research B10 was for the Planetary Data System titles); kept here word for word: "- (b) Is there a rule that holds across the catalog? For example: in a Planetary Data System title, such as "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0", the first word is the spacecraft that carried the instrument (what the Planetary Data System calls the instrument host); in "MODIS/Aqua", the word after the instrument is the spacecraft; and a word is a Mission only where the record calls it a mission." Option 4, as it was: "A rule for each part of the catalog, such as the one in (b)." My current reading, as it was: "Option 1, because it follows the record's own words and adds nothing the record doesn't state. We would move to option 4 if your answer to (b) gives a rule that holds across the catalog, since the choice would then be the same for every record."

Checked on 2026-10-31, for the titles of Earth science records: in the MODIS products' own metadata (NASA's Common Metadata Repository, UMM-C `Platforms`), the word after "MODIS/" is the platform: MYD10_L2 lists "Aqua" (https://cmr.earthdata.nasa.gov/search/concepts/C3090964320-NSIDC_CPRD.umm_json), MOD11A1 "Terra" (https://cmr.earthdata.nasa.gov/search/concepts/C2763297212-LPCLOUD.umm_json), MCD19A2 both (https://cmr.earthdata.nasa.gov/search/concepts/C2324689816-LPCLOUD.umm_json); the NSIDC user guide's file-name table reads "MYD MODIS/Aqua". But it is a pattern of one family of titles: the OBPG's "MODIS Aqua Level 3 SST …" has no slash (platform "Aqua", https://cmr.earthdata.nasa.gov/search/concepts/C2036881966-POCLOUD.umm_json), and "Aquarius L3 …" starts with the instrument, whose platform is "SAC-D" (https://cmr.earthdata.nasa.gov/search/concepts/C2791494051-NSIDC_CPRD.umm_json). The same CMR records list "Terra" (MOD11A1) and "Terra" and "Aqua" (MCD19A2) as projects too, so NASA uses one word for the craft and the mission; that is now in the Context. Decided on 2026-10-31: with research B10 (no Planetary Data System title convention in rule 1's closed list, docs/improvements.md, *Considered and not changed*), no rule holds for the whole catalog, only clues per family of titles, which stay the annotator's clues for the entity class; no new convention in rule 1, and no ground truth triple changes.

Checked on 2026-10-31, the old (c) above: our reading holds. NASA: "NASA's Aquarius was the primary instrument on the SAC-D spacecraft" (https://science.nasa.gov/mission/aquarius/); PO.DAAC: the Aquarius/SAC-D mission "was a joint venture between NASA and the Argentinean Space Agency (CONAE)" (https://podaac.jpl.nasa.gov/aquarius); NASA's metadata gives the platform "SAC-D" and the instrument "AQUARIUS_RADIOMETER" (CMR, above). So the ground truth's Instrument "Aquarius L-band radiometer" and Mission "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" stand, and no Spacecraft is written: the record names SAC-D only inside the mission's name (rule 1 of *What counts as a fact*).

Checked on 2026-10-31, for the expert's (a), how the field's lists read a bare "Aqua": NASA's Global Change Master Directory (GCMD) files "Aqua" ("Earth Observing System, Aqua") and "Terra" ("Earth Observing System, Terra (AM-1)") as platforms, under Space-based Platforms, Earth Observation Satellites (GCMD Platforms keywords, version 25.1, https://gcmd.earthdata.nasa.gov/KeywordViewer/); NASA's Aqua page calls it "a NASA Earth Science satellite mission" (https://science.nasa.gov/mission/aqua/); Wikidata has one item for each, the spacecraft (Aqua, Q17397, "NASA Earth observation satellite"), with the mission's facts on it. So where a metadata standard has to choose, a bare "Aqua" or "Terra" is the platform, the spacecraft; in ordinary use one name serves both. Option 1 stays; the graph side (one node, or a Mission and a Spacecraft linked) is in docs/improvements.md, *Mission or spacecraft, when they share a name*.

Checked on 2026-10-31, for the expert's (a), the Planetary Data System's own registry (its PDS4 context products, https://pds.nasa.gov/data/pds4/context-pds4/): it gives a bare name to both. "DAWN" is another name of both the spacecraft (`spacecraft.dawn`, "The Dawn Spacecraft", type Spacecraft) and the mission (`mission.dawn_mission_to_vesta_and_ceres`, "The Dawn Mission to Vesta and Ceres", type Mission); "STARDUST" of both `spacecraft.sdu` and `mission.stardust`; but "ROSETTA-ORBITER" only of the spacecraft (`spacecraft.ro`, "The Rosetta Orbiter Spacecraft"), the mission's other names being "ROSETTA" and "INTERNATIONAL ROSETTA MISSION". GCMD likewise has "Aqua" and "Terra" both as platforms and as projects, and NASA CMR's record of MOD11A1 lists "Terra" as its platform and as its project. So the field's own lists leave a bare name ambiguous, and in a Planetary Data System title its position (the instrument host) settles it. This informs options 1 and 3; the reading stays with the experts, and the record's words and their position decide (rule 1 of *What counts as a fact*).

Checked again on 2026-10-31, the old (c) above, against GCMD and CMR: GCMD's Platforms list has "SAC-D | Satélite de Aplicaciones Científico - D" (Earth Observation Satellites), and its Projects list both "AQUARIUS" and "AQUARIUS SAC-D"; CMR's record of AQUARIUS_L3_SSS_SMI_7DAY_V5 names the platform "Aquarius_SAC-D" (not "SAC-D"), the instruments AQUARIUS_RADIOMETER and AQUARIUS_SCATTEROMETER, and the project "AQUARIUS SAC-D". So NASA's own metadata mixes the names; the record's words ("Aquarius L-band radiometer") stay as written.

### Quoted for us

- entity class Instrument: a device that takes measurements
- predicate ABOARD: is carried on
- entity class Mission -> Mission: A planned space or flight undertaking, such as a satellite mission, balloon program, or spaceflight of a given duration, carried out to accomplish scientific objectives.
- entity class Spacecraft -> Platform: A vehicle or platform, such as a satellite, aircraft, or balloon, that carries instruments to collect observations.
- Writing a classed triple, rule 11: Subject instance and object instance: the record's own words, as written.
- Writing a classed triple, rule 14: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 23: One thing, one wording, within a record.

### Consequences

#### Option 1: Spacecraft where the words name the craft, Mission where they name the mission

- No change to the ground truth triples listed under Affects, nor to the annotation guidelines.
- Each record needs a judgment, made from clues in its own words; two people may judge the same word differently, and so may the [model](../docs/terminology.md#8-the-pipeline) when it extracts.
- A search of the knowledge graph for "all data from DAWN" has to look under both FROM_MISSION and FROM_SPACECRAFT.

#### Option 2: Always Mission

- One choice for every record: easier to apply the same way.
- The ground truth triples with FROM_SPACECRAFT (listed under Affects) change to FROM_MISSION ("DAWN", "Aqua", "ROSETTA-ORBITER", "Terra").
- "MODIS" ABOARD "Aqua" (the records "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" and "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0") would join an Instrument to a Mission, which ABOARD's definition ("is carried on") doesn't fit: a mission doesn't carry an instrument.

#### Option 3: Both, a Mission and a Spacecraft

- A search finds the data under either predicate.
- Against "What counts as a fact", rule 1 (quoted above): a record that names only the craft doesn't state the mission, so the second ground truth triple adds what we know from elsewhere.
- The ground truth gets more ground truth triples per record, and the model would be expected to write both too.

#### Option 4: A rule by where the record comes from

- The same words are always read the same way within each part of the catalog.
- The rule has to be written into the annotation guidelines and into the copy of the rules the model follows, and it would hold for one family of titles only (My notes, 2026-10-31).

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 10: 3bceffb4-f01e-433c-af79-42b9d9427231
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- record at pool position 21: 264a9b23-9a86-46a7-ab61-9661230ea667
- record at pool position 16: ec41fd5d-1159-4aa8-9803-5346e2324a20
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 22: 967275c7-aa2d-4b08-a9db-aff5cf6b7802
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_PLATFORM "ROSETTA-ORBITER" (Platform)
- classed triple of the record at pool position 2: "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Platform)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) FROM_MISSION "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission)
- classed triple of the record at pool position 4: "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Platform)
- classed triple of the record at pool position 4: "Aqua" (Platform) FLIES_IN "A-train" (SatelliteFormation)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the atmosphere" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the land" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the oceans" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_TARGET "Earth" (CelestialBody)
- classed triple of the record at pool position 4: "Aqua" (Platform) LAUNCHED_BY_PARTY "NASA" (Organization)
- classed triple of the record at pool position 4: "Aqua" (Platform) LAUNCHED_ON "May 4, 2002" (Time)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) FROM_PLATFORM "DAWN" (Platform)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_PLATFORM "Terra" (Platform)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) FROM_PLATFORM "Terra" (Platform)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) FROM_MISSION "Stardust-NExT" (Mission)
- classed triple of the record at pool position 9: "Stardust-NExT" (Mission) ENDED_ON "March, 2011" (Time)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) FROM_PLATFORM "STARDUST" (Platform)
- classed triple of the record at pool position 10: "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (Dataset) FROM_PLATFORM "Rosetta Orbiter" (Platform)
- classed triple of the record at pool position 10: "Rosetta Orbiter ALICE UV Spectrometer" (Instrument) ABOARD "Rosetta Orbiter" (Platform)
- classed triple of the record at pool position 12: "2XMMi-DR3" (Dataset) FROM_PLATFORM "XMM-Newton" (Platform)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) FROM_PLATFORM "XMM-Newton" (Platform)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) FROM_PLATFORM "ROSETTA-ORBITER" (Platform)
- classed triple of the record at pool position 13: "OSIRIS Narrow Angle Camera" (Instrument) ABOARD "ROSETTA-ORBITER" (Platform)
- classed triple of the record at pool position 4: "Aqua" (Platform) FLIES_IN "Earth Observation Satellites (EOS)" (SatelliteFormation)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) FROM_MISSION "BARREL" (Mission)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "study electron losses from Radiation Belts" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_TARGET "Earth" (CelestialBody)
- classed triple of the record at pool position 19: "BARREL" (Mission) PART_OF "NASA Living with a Star" (Organization)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "augment the Radiation Belt Storm Probes, RBSP, mission" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "providing measurements of the spatial variations of electron precipitation from the radiation belts" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "providing measurements of the temporal variations of electron precipitation from the radiation belts" (Purpose)
- classed triple of the record at pool position 19: "Radiation Belt Storm Probes, RBSP" (Mission) ALSO_KNOWN_AS "Van Allen Probes" (Mission)
- classed triple of the record at pool position 19: "August 2015 BARREL campaign" (Campaign) COORDINATED_WITH "Radiation Belt Storm Probes, RBSP" (Mission)
- classed triple of the record at pool position 19: "2016 campaign" (Campaign) COORDINATED_WITH "Radiation Belt Storm Probes, RBSP" (Mission)
- classed triple of the record at pool position 19: "2013 balloon campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "2014 balloon campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "August 2015 BARREL campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "2016 campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_NUMBER_OF "four BARREL campaigns" (Value)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_NUMBER_OF "over 50 small, approximately 20 kg, stratospheric balloons" (Value)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_TIME_SPAN "from 2013 to 2016" (Time)
- classed triple of the record at pool position 21: "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (Dataset) FROM_MISSION "Chandrayaan-1" (Mission)
- classed triple of the record at pool position 21: "Chandrayaan-1" (Mission) HAS_TARGET "Moon" (CelestialBody)
- classed triple of the record at pool position 16: "Plasma Wave Spectrometer (PWS)" (Instrument) ABOARD "Voyager 1" (Platform)
- classed triple of the record at pool position 16: "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (Dataset) FROM_PLATFORM "Voyager 1" (Platform)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) FROM_PLATFORM "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)" (Platform)
- classed triple of the record at pool position 19: "X-ray spectrometer" (Instrument) ABOARD "BARREL balloon" (Platform)
- classed triple of the record at pool position 19: "DC magnetometer" (Instrument) ABOARD "BARREL balloon" (Platform)
- classed triple of the record at pool position 19: "BARREL balloon" (Platform) HAS_MASS "approximately 20 kg" (Value)
- classed triple of the record at pool position 22: "Flight Data For Tail 655" (Dataset) FROM_PLATFORM "Tail 655" (Platform)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) FROM_PLATFORM "Aura" (Platform)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) FROM_PLATFORM "Sentinel-1" (Platform)
- classed triple of the record at pool position 25: "Sentinel-1 radar observations" (Dataset) FROM_PLATFORM "Sentinel-1" (Platform)
- translation table row: entity class Mission
- translation table row: entity class Spacecraft
- translation table row: entity class SpaceStation
- translation table row: predicate SOURCED_FROM
- translation table row: predicate OBSERVED_BY
- ground truth schema entry: entity class Mission
- ground truth schema entry: entity class Platform
- ground truth schema entry: predicate FROM_MISSION
- ground truth schema entry: predicate FROM_PLATFORM
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 11
- rule: Writing a classed triple, rule 14
- rule: Writing a classed triple, rule 23
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which follows any change to them

## Q3: Variable or PhysicalQuantity: what is measured, and what is computed?

- status: open
- priority: high
- question kind: schema entry
- in short: the ground truth schema's Variable and PhysicalQuantity, and HAS_MEASUREMENTS_OF, HAS_VARIABLE and ESTIMATES

### The question

Our schema separates two things a dataset can hold: a PhysicalQuantity, a bare property that any method could measure (temperature, sea surface temperature, snow cover), and a Variable, a property narrowed by a method, a band, a threshold or another constraint (SST4, NDSI, band 31 emissivity). A dataset HAS_MEASUREMENTS_OF a PhysicalQuantity and HAS_VARIABLE a Variable, and a Variable ESTIMATES a PhysicalQuantity (all defined below). The example shows the line as we draw it: one record's sea surface temperature, and two named products that estimate it, SST4 and NSST. We are not sure where the line falls for an index:

- (a) Is an index such as the Normalized Difference Snow Index (NDSI), which the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says "is derived from radiance data", a Variable (a property narrowed by the bands it is computed from), or a kind of thing of its own?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: global NASA skin sea surface temperature (SST) products
- source text: SST MID-IR
- source text: skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST
- source text: the SST derived from these measurements is identified as SST4
- source text: At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_MEASUREMENTS_OF "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VARIABLE "SST4" (Variable)
- classed triple: "skin SST" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)

### Ground truth schema

- entity class PhysicalQuantity: a bare property that can be measured, whatever method measures it, e.g. temperature; gravity; sea surface temperature; snow cover; not a form the data take, such as images, image cubes, spectra or maps (a SpatialRepresentation)
- entity class Variable: a property narrowed by a method, a band, a threshold, another object or another constraint, e.g. SST4; NDSI; band 31 emissivity; dust fluences at each of twelve mass thresholds
- predicate HAS_MEASUREMENTS_OF: holds measurements of this PhysicalQuantity
- predicate HAS_VARIABLE: holds this Variable in its files
- predicate ESTIMATES: gives approximate values for

### Options

#### Option 1: Keep the line as the definitions draw it

A PhysicalQuantity for a bare property of what is observed (snow cover, sea surface salinity, gravity, aerosol optical depth); a Variable for a property narrowed by a method, a band, a threshold or another constraint (SST4, NDSI, the count rates, the band 31 emissivity).

#### Option 2: An entity class of its own for an index

An entity class for an index computed from other values (the NDSI), apart from Variable and PhysicalQuantity.

### My current reading

Option 1, because the two definitions already separate what is measured from the values an algorithm computes, and the records we have read fit them. Your answer to (a) decides whether an index needs an entity class of its own (option 2).

### My notes

Checked against sources on 2026-10-30: the NDSI is a computed index, "NDSI = ((band 4-band 6) / (band 4 + band 6))" (NSIDC, MODIS snow user guide, https://nsidc.org/sites/default/files/c61_modis_snow_user_guide.pdf). "Global Gravity", "Occultation" and "Solar Conjunction" are values of the label keyword OBSERVATION_TYPE in the Rosetta radio science data (ESA archive catalog files, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/); gravity is inferred from radio tracking (Doppler and range), not measured directly.

Six of the [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) we have annotated so far hold a PhysicalQuantity or a Variable (the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" is in the ground truth now); their classed triples that say what the dataset holds, and what a value was computed from, are listed under Affects. The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0". The others named: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (the "Global Gravity" sentence), "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (the NDSI), "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (the salinity retrievals), "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (the count rates), "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (the aerosol optical depth, the atmospheric properties and the view geometry).

Approved on 2026-10-25, for the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (fact 13): HAS_MEASUREMENTS_OF "atmospheric properties" and HAS_MEASUREMENTS_OF "view geometry", source text "The MCD19A2N product provides the atmospheric properties and view geometry"; sub-question (g) below (now part of the expert's (b)) asks the two doubts about them.

Decided on 2026-10-25, for us to confirm, for the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006": its four supporting layers, each HAS_MEASUREMENTS_OF a PhysicalQuantity, as for the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (sub-question (g)); its two band emissivities, each HAS_MEASUREMENTS_OF a PhysicalQuantity and COMPUTED_FROM "land cover types" (sub-question (h)). The four supporting layers: confirmed on 2026-10-31 as what the files hold, and written with a predicate of their own (below). The two band emissivities: settled on 2026-10-31 (below: Variables, each narrowed by its band; "land cover types" stays a PhysicalQuantity, the old (h)).

Decided on 2026-10-31, with the new definitions of PhysicalQuantity ("a bare property that can be measured, whatever method measures it, e.g. temperature; gravity; sea surface temperature; snow cover") and Variable ("a property narrowed by a method, a band, a threshold, another object or another constraint, e.g. SST4; NDSI; band 31 emissivity; dust fluences at each of twelve mass thresholds"): the two band emissivities are Variables, each narrowed by its band, which settles the Variable half of the old (h) below: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_VARIABLE "band 31 emissivity" (Variable) and "band 31 emissivity" (Variable) COMPUTED_FROM "land cover types" (PhysicalQuantity), and the same for band 32 (before: HAS_MEASUREMENTS_OF, and "band 31 emissivity" (PhysicalQuantity)). What kind of thing "land cover types" is, the rest of the old (h), is still open. By the same definitions, three more are Variables now: "RDR data" (Dataset) HAS_VARIABLE "dust fluences at each of twelve mass thresholds" (Variable), narrowed by thresholds (the record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0"), and "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_VARIABLE "Ensemble X-Ray Variability" (Variable), narrowed by the sources it is taken over (the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3"); both were HAS_MEASUREMENTS_OF a PhysicalQuantity. And the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" now has "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_SPATIAL_REPRESENTATION "solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data" (SpatialRepresentation), in place of "image data in W/m^2/sr/nm" (rule 24: the words that name no method stay in the instance; rule 22: describing words joined by "and" or a comma stay whole); the old (i) below is still open.

Decided on 2026-10-25, for us to confirm, for the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3": its HAS_MEASUREMENTS_OF "redshifts" and "spectral classifications", each a PhysicalQuantity (sub-question (j)). Confirmed on 2026-10-31 (below, the old (j)): both stay as the record gives them.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as they were. The expert's (a) now holds the old (a), (b), (d) and (f); their (b) the old (c), (g), (i) and (j); their (c) the old (e). Left for us: the reading of how the snow cover is made (in the old (b)), and the old (h), both to check against a source (the MODIS snow and land surface temperature products' own documents) or to settle once (a) and (b) are answered.

- (a) Is the line right as the two definitions draw it: a PhysicalQuantity is a property of the thing observed, which any method could measure; a Variable is one named product of one algorithm?
- (b) The Normalized Difference Snow Index (NDSI, in the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061") is an index computed from radiances. Is it a Variable, or something of its own (an index), neither a Variable nor a PhysicalQuantity? And is our reading of how the snow cover is made right: the NDSI is computed from the radiance data (by a method the record doesn't name), and the snow cover from the NDSI by "a series of screens"?
- (c) "fast neutron residual count rates" (in the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0") are rates an instrument counts, not a property of Vesta. Are they a Variable, or a third thing: what the instrument recorded, before it is turned into a property of the body? The same record says "The nominal fast neutron count rates were detrended", and the ground truth writes "nominal fast neutron count rates" as a Variable too. Those are the counts as the instrument recorded them, before any processing, which sits badly with a Variable's "computed from an Instrument's measurements by one particular Algorithm": what are they?
- (d) "Sea Surface Salinity (SSS) retrievals" (in the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005") is written down as "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_MEASUREMENTS_OF "Sea Surface Salinity (SSS)" (PhysicalQuantity). Should every quantity a record calls a "retrieval" be a Variable instead, since an algorithm computed it?
- (e) The record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" says "It is a Global Gravity measurement at the comet 67P", and we wrote "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_MEASUREMENTS_OF "Gravity" (PhysicalQuantity) and "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_SPATIAL_COVERAGE "Global" (SpatialExtent). Is "Gravity" the quantity measured (the comet's gravity field)? Or is "Global Gravity" the name of a kind of radio science measurement, as a whole, beside "Occultation" and "Solar Conjunction", which other records of the catalog name in the same sentence? If these are kinds of measurement: what is measured in each, in plain words (for example, our reading, not checked against a source: an occultation measures the atmosphere the radio signal passes through)?
- (f) "Aerosol Optical Depth" (in the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid") is what the record's product holds, computed by MAIAC ("Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product"). We wrote it as a PhysicalQuantity, a property of the atmosphere that other methods could measure too, and MAIAC as the method. Is that right, or is it a Variable, since one algorithm computed it?
- (g) The same record says "The MCD19A2N product provides the atmospheric properties and view geometry", and we wrote "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "atmospheric properties" (PhysicalQuantity) and "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "view geometry" (PhysicalQuantity). Is "atmospheric properties" specific enough to be a fact, or too vague to write down? And is "view geometry" (the angles between the sun, the satellite and the ground) a PhysicalQuantity, something measured, or supporting information the files hold, which would need another entity class or predicate? The record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" lists more of the same kind: "Provided along with the daytime and nighttime surface temperature bands are associated quality control assessments, observation times, view zenith angles, and clear-sky coverages". We wrote them the same way, each a PhysicalQuantity the dataset HAS_MEASUREMENTS_OF ("quality control assessments", "observation times", "view zenith angles", "clear-sky coverages"); quality control assessments and observation times stretch "a property that can be measured" further still. Should these be written as something the files hold, rather than as measurements?
- (h) The same record goes on: "along with bands 31 and 32 emissivities from land cover types". We wrote "band 31 emissivity" (PhysicalQuantity) COMPUTED_FROM "land cover types" (PhysicalQuantity), and the same for band 32, reading "from" as: each pixel's emissivity is estimated from its type of land cover (our reading, not checked against a source). Is that reading right? If so, are emissivities estimated that way Variables rather than PhysicalQuantities, and what kind of thing is "land cover types": a PhysicalQuantity, an input dataset, or something else?
- (i) The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" holds "image data in W/m^2/sr/nm", which we wrote as "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_MEASUREMENTS_OF "image data in W/m^2/sr/nm" (PhysicalQuantity), keeping the unit in the instance. Image data are not a property; our reading, not checked against a source, is that the unit is that of a spectral radiance, which the record doesn't name. What should be written: the images as the layout of the data, the unit as a fact of its own, or something else?
- (j) The record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" says its sources were matched with a quasar catalog "to obtain redshifts and spectral classifications for the sources". We wrote "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_MEASUREMENTS_OF "redshifts" (PhysicalQuantity) and the same with "spectral classifications" (PhysicalQuantity). A redshift is a property that can be measured. Is a spectral classification (the label a source's spectrum is given, such as the type of quasar) a PhysicalQuantity too, or a label of its own?

The question's context, as it was: The example below holds both: a PhysicalQuantity, and two Variables that estimate it. The record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says its snow cover is "detected using Normalized Difference Snow Index (NDSI) and a series of screens", and "The NDSI is derived from radiance data"; the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "These data are maps of fast neutron residual count rates"; and the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" says "Aquarius L-band radiometer Sea Surface Salinity (SSS) retrievals".

The sentence of the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" recurs across the catalog. We counted it in the records of the catalog (020's records.jsonl, 36,406 records, harvested before 2026-10-24): "It is a Global Gravity measurement" in 2,835 records (2,442 of them "at the comet 67P"), "It is a Occultation measurement" in 439, "It is a Solar Conjunction measurement" in 240, and "It is a Phobos Gravity measurement" in 9. Since "Phobos Gravity" sits beside "Global Gravity", our reading is that the word before "Gravity" says which gravity measurement it is, not an area; but we don't know. (Whether "Global" can be an area at a comet at all, we ask separately; here the question is only what is measured.)

Taken out of the expert's (b) on 2026-10-26, because it named five records in one paragraph; kept here word for word. The expert's (b) now shows two cases, each with its record: the count rates (the old (c)) and the supporting layers of the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (part of the old (g)). The images with their unit, the atmospheric properties and view geometry, and the redshifts and spectral classifications stay for us, as the old (i), the old (g) and the old (j) above say them.

- The expert's (b), as it was: Some things a dataset holds are not a property of what is observed. What should each be? Counts as the instrument recorded them: "maps of fast neutron residual count rates" (the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0"; we wrote a Variable). Images with their unit: "image data in W/m^2/sr/nm" (the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0"). Supporting layers: "quality control assessments, observation times, view zenith angles, and clear-sky coverages" (the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006") and "atmospheric properties and view geometry" (the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid"). Labels: "redshifts and spectral classifications" (the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3"). Except for the count rates, we wrote each as a PhysicalQuantity the dataset has measurements of.

Taken out of the expert's view on 2026-10-31, as a question we can settle from sources; kept here word for word. The (c) ended: "If these are kinds of measurement, what does each measure, in plain words?" The archive's own description of the instrument answers it (the RSI data set's INST.CAT, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/, checked on 2026-10-30): an occultation records the radio signal as it passes through the coma when the spacecraft goes behind the comet, "leading to profiles of pressure for neutral particles and profiles of electron density for plasma. In addition the exact size and shape of the shape of the comet can be derived"; a solar conjunction records the signal as it passes through the solar corona ("Solar scintillation and Faraday rotation experiments were conducted to improve understanding of the structure and dynamics of the solar corona and wind"); and a gravity measurement gives the body's gravity field, inferred from tracking ("Range and Doppler measurements are used to calculate the spacecraft trajectory and to infer gravity fields of objects near the spacecraft"). "Global" against "Target" gravity is defined by the same team's Mars Express data sets: global gravity measurements "were conducted around apocenter and target gravity measurements which were conducted around pericenter over interesting geophysical structures" (https://pds-geosciences.wustl.edu/mex/mex-m-mrs-1_2_3-ext2-v1/mexmrs_2603/catalog/dataset.cat); that it means the same for Rosetta is my reading.

The question's opening, as it was: "Our schema separates two things a dataset can hold: a PhysicalQuantity, a property that any method could measure (sea surface temperature, snow cover), and a Variable, one named value that one algorithm computes (SST4, NDSI)." Option 1, as it was: "A PhysicalQuantity for a property of what is observed (snow cover, sea surface salinity, gravity, aerosol optical depth); a Variable for a named value one algorithm computes (SST4, NDSI, the count rates)."

Changed on 2026-10-31, by rule 24's *Words that name no method* ("It gives no ground truth triple, and it stays in the instance, as written"): "retrievals" names no method, so it stays in the instance: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_MEASUREMENTS_OF "Sea Surface Salinity (SSS) retrievals" (PhysicalQuantity), in place of "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_MEASUREMENTS_OF "Sea Surface Salinity (SSS)" (PhysicalQuantity). Whether a retrieval is a Variable is still the old (d), above.

Taken out of the expert's view on 2026-10-31 (the research of 2026-10-31, and my decisions of that day); kept here word for word. The question's opening ended "We are not sure where the line falls in other records:". The sub-questions were: "- (a) Is a quantity that a record says an algorithm computed still a PhysicalQuantity, or a Variable? We wrote both of these as PhysicalQuantities: "Sea Surface Salinity (SSS) retrievals" (the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005") and "Aerosol Optical Depth", computed by "Multi-Angle Implementation of Atmospheric Correction (MAIAC)" (the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid"). And is an index such as the Normalized Difference Snow Index (NDSI), which the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says "is derived from radiance data", a Variable, or something of its own?" "- (b) Some things a dataset holds are not a property of what is observed. What should each be? First, counts as the instrument recorded them: the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "These data are maps of fast neutron residual count rates", and we wrote the count rates as a Variable. Second, layers that come with the data: the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" says "Provided along with the daytime and nighttime surface temperature bands are associated quality control assessments, observation times, view zenith angles, and clear-sky coverages", and we wrote each of the four as a PhysicalQuantity the dataset has measurements of." "- (c) Many records say "It is a Global Gravity measurement at the comet 67P" (one is the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0"); others, in the same sentence, say "Phobos Gravity", "Occultation" or "Solar Conjunction". We wrote "Gravity" as what is measured and "Global" as the area covered. Or is "Global Gravity" the name of one kind of radio science measurement, as a whole?" The first half of the old (a) is settled from the field's practice, and its second half is the expert's (a) now; the old (b) and (c) are decided (below). Options 3 to 5, as they were: Option 3: Every computed quantity is a Variable: A quantity the record says was retrieved or computed (the salinity retrievals, the aerosol optical depth MAIAC computes) is a Variable; a PhysicalQuantity only where the record names the property alone. Option 4: An entity class of its own for what an instrument records: An entity class for what the instrument itself records, before any conversion (count rates, radiances), apart from Variable. Option 5: A kind of measurement of its own: An entity class for a kind of measurement, with "Global Gravity", "Occultation" and "Solar Conjunction" as its instances; what is measured (gravity, for example) stays a PhysicalQuantity, where the record names it. Their consequences, as they were: Option 3: Every computed quantity is a Variable: - The ground truth triple with "Sea Surface Salinity (SSS)" (the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005") changes to HAS_VARIABLE, a Variable, and so does "Aerosol Optical Depth" (the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid"). - Almost every value in a satellite dataset is computed by some algorithm, so most PhysicalQuantities would become Variables, and a search for "salinity data" would have to look under both. - The annotation guidelines, and the model's copy of their rules, say when a quantity counts as computed. Option 4: An entity class of its own for what an instrument records: - The ground truth triples with the count rates (the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0") change their entity class, and perhaps "radiance data" (the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061"). - One more distinction for the annotation guidelines, and it holds only if the expert's answer to (b) confirms it. Option 5: A kind of measurement of its own: - The ground truth triples of the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" with "Gravity" and with "Global" become one ground truth triple with "Global Gravity" (rule 19 of *Writing a classed triple*: "Global" stays in the instance if it is no area). - A new entity class and predicate in the ground truth schema; the model must learn to tell a kind of measurement from a quantity measured. - If the expert's answer to (c) is that "Global Gravity" is a name as a whole but still something measured, it stays a PhysicalQuantity instead, "Global Gravity", with the same change to the two ground truth triples. My current reading, as it was: "Option 1, because the two definitions already separate what is measured from the values an algorithm computes, and most records we have read fit them; "Aerosol Optical Depth" stays a PhysicalQuantity, since our reading is that other methods measure it too. Your answers to (a) and (b) decide whether the NDSI and the count rates need an entity class of their own (options 2 and 4). For (c), we lean towards "Global Gravity" as a whole (option 5), because "Phobos Gravity" in other records reads like the same kind of name, with no area in it."

Checked on 2026-10-31, the first half of the old (a): the field names a quantity by what it is, not by how it was got. The CF conventions' standard name sea_surface_salinity: "the unqualified term 'salinity' is generic and does not necessarily imply any particular method of calculation" (the CF standard name table, https://cfconventions.org/Data/cf-standard-names/current/src/cf-standard-name-table.xml); atmosphere_optical_thickness_due_to_ambient_aerosol_particles is one standard name, with no method in it. RDA's I-ADOPT framework: "The Variable describes WHAT has been observed, measured, simulated, or calculated independently of WHERE …, HOW (procedure, protocol) and WHEN" (Magagna et al., "The I-ADOPT Interoperability Framework for FAIRer data descriptions of biodiversity", arXiv:2107.06547). So "Sea Surface Salinity (SSS) retrievals" and the aerosol optical depth MAIAC computes stay PhysicalQuantities, as option 1 has them (our reading that other methods measure it too is now checked); old option 3 has no support. For an index, CF's normalized_difference_vegetation_index says "The calculated value of NDVI depends on the precise definitions of the spectral bands": a quantity tied to its bands, which our Variable's "narrowed by … a band" covers (the NDSI has no CF standard name; the NDVI is the parallel case, my reading). No standard I found gives an index a class of its own, so the expert's (a) asks only that.

Decided on 2026-10-31, the old (b), the supporting layers: they are not measurements of what is observed, and the field keeps them apart. The CF conventions call them ancillary data, "When one data variable provides metadata about the individual values of another data variable", for example "quality flags indicating the results of a quality control test" (CF 1.11, section 3.4, *Ancillary Data*, https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html); a view zenith angle is a quantity of the viewing, not of the land (CF's sensor_zenith_angle: "the angle between the line of sight to the sensor and the local zenith at the observation target"); and the Planetary Data System keeps "data that are supplementary to observational data" in products of their own (PDS4's Product_Ancillary, https://pds.nasa.gov/datastandards/documents/dd/v1/PDS4_PDS_DD_1P00.html). So a new predicate of the ground truth schema, HAS_ANCILLARY_DATA, "holds this supporting information about its values, such as quality flags or viewing geometry", next to HAS_VARIABLE. Its object is a Variable, the entity class HAS_VARIABLE takes: each layer is a property of another object (the values, or the view), a Variable's "narrowed by … another object", and CF calls such layers ancillary variables; it is pinned to Variable, as HAS_VARIABLE is. The record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" now has "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "quality control assessments" (Variable), and the same for "observation times", "view zenith angles" and "clear-sky coverages" (each was HAS_MEASUREMENTS_OF a PhysicalQuantity); the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" now has "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_ANCILLARY_DATA "view geometry" (Variable) (was HAS_MEASUREMENTS_OF "view geometry" (PhysicalQuantity)); its "atmospheric properties" stay HAS_MEASUREMENTS_OF, the retrieved quantities. NASA's metadata lists what MCD19A2 holds: "blue band AOD at 0.47 µm, green band AOD at 0.55 µm, AOD uncertainty, fine mode fraction over water, column water vapor over land and clouds (in cm), smoke injection height (m above ground), AOD QA, AOD model at 1km, cosine of solar zenith angle, cosine of view zenith angle, relative azimuth angle, scattering angle, and glint angle at 5km" (https://cmr.earthdata.nasa.gov/search/concepts/C2324689816-LPCLOUD.umm_json); that list is for 080's enrichment. The count rates: the field agrees with a Variable (W3C SOSA calls what a sensor returns a Result, "The Result of an Observation, Actuation, or act of Sampling", https://www.w3.org/TR/vocab-ssn/; no standard gives what an instrument records a class of its own), so old option 4 has no support.

Decided on 2026-10-31, the old (c): "Global Gravity" is one name, the archive's value for a mode of measurement, and stays whole (rule 11 of *Writing a classed triple*: "rules 19, 22 and 24 never split or shorten a name"). It reverses the decision of the same day to keep the split until the experts answered (research B3; docs/improvements.md, *Considered and not changed*), on new evidence, checked on 2026-10-31. The data set's Level 2 labels have OBSERVATION_TYPE = "GLOBAL GRAVITY"; the radio science team's naming document, shared by Mars Express, Venus Express and Rosetta, defines the keyword: "Observation_Type | Mode of the executed measurement. Possible values are: Commissioning, Occultation, Target Gravity, Global Gravity, Solar Conjunction, Bistatic Radar, Phobos Gravity" (ROS-RSI-IGM-IS-3087, in the data set's DOCUMENT/RSI_DOC folder, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/DOCUMENT/RSI_DOC/); the PDS3 data dictionary gives the keyword no standard values (https://pds.nasa.gov/data/pds4/documents/document_pds3_standards/psdd_rev_F_20080611.pdf), so these are the team's own. The word before "Gravity" is not always an extent: "Phobos Gravity" is Mars Express's measurement of Phobos's mass from close flybys, "When the distance between orbiter and Phobos is < 500 km Mars Radio Science will be able to derive the mass and density of the moon" (the inst.cat of the data set MEXMRS_2346, https://pds-geosciences.wustl.edu/mex/mex-m-mrs-1_2_3-ext2-v1/mexmrs_2346/catalog/inst.cat, whose target is PHOBOS; all nine catalog records with it are "MARS EXPRESS PHOBOS MRS …"), which settles our "we don't know" above. No Rosetta document defines Global against Target gravity, and the Rosetta archive has no Target Gravity volume (my count of the 1149 volume's AAREADME table: 946 Global Gravity volumes, none Target Gravity); the nearest is the RSI user manual's Gravity Mapping Campaign, "Objective: Nucleus gravity field", with the activity "global gravity with TM OFF" (RO-RSI-IGM-MA-3081, same folder). What "Global" means at a comet, the field of the whole nucleus, is my reading. Of the catalog's 2,835 "Global Gravity" records, 393 are Mars Express's, where the team's definition above applies. The entity class: Variable, since "Global Gravity" is gravity narrowed by a constraint, its scope (I-ADOPT's Constraint "limits the scope of the observation and confines the context to a particular state", https://w3id.org/iadopt/ont), not "a bare property", as PhysicalQuantity's definition asks; so the predicate is HAS_VARIABLE, since HAS_MEASUREMENTS_OF is pinned to PhysicalQuantity. The record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" now has "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_VARIABLE "Global Gravity" (Variable), in place of "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_MEASUREMENTS_OF "Gravity" (PhysicalQuantity), and "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_SPATIAL_COVERAGE "Global" (SpatialExtent) is deleted. No entity class for a kind of measurement (old option 5) is coined: the Variable holds the name, and no other record needs one.

Checked on 2026-10-31, the notes left for us above. The old (h): the emissivities are estimated from land cover types, as we read it: "Emissivity values in bands 31 and 32 are estimated by the classification-based emissivity method (Snyder and Wan, 1998) according to land cover types in the pixel determined by the input data in Land Cover (MCDLC1KM) and daily Snow Cover (MOD10_L2)" (Wan, *MODIS Land Surface Temperature Products Users' Guide*, Collection 6.1, https://modis-land.gsfc.nasa.gov/pdf/MOD11_User_Guide_V61.pdf). "land cover types" stays a PhysicalQuantity, a property of the surface that several methods classify; the input product MCDLC1KM is not written, since the record doesn't name it (rule 1 of *What counts as a fact*). The old (i): the archive calls the unit "radiance units (W m-2 sr-1 nm-1)" (*OSIRIS calibration pipeline OsiCalliope*, OSIRIS_CAL_PIPELINE_V08.PDF, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/OSINAC/RO-C-OSINAC-4-ESC3-67P-M20-INFLDSTR-V1.0/DOCUMENT/CALIB/); radiance per unit wavelength is a spectral radiance (my reading, standard physics); the record names no quantity, so the instance stays as written (rule 1). The old (j): SDSS classifies spectra into groups, "The calibrated spectra are classified into various groups (e.g., star, galaxy, quasar)" (Schneider et al., "The Sloan Digital Sky Survey Quasar Catalog. V. Seventh Data Release", AJ 139, 2360, arXiv:1004.1167), so a spectral classification is a label, not a bare property; but the record says only that the authors obtained both "for the sources", and the table's file has a redshift column and no classification column (the CDS ReadMe of J/A+A/536/A84, read through the NAO mirror, http://vizier.nao.ac.jp/ftp/cats/J/A+A/536/A84/ReadMe), so "spectral classifications" stays as the record's words give it, beside "redshifts": outside knowledge doesn't decide a triple the record gives for both alike. Whether a label needs an entity class of its own is ours to settle once another record needs one. The snow cover (the old (b)): our reading matches the snow user guide, "NDSI = ((band 4-band 6) / (band 4 + band 6))", then thresholds and data screens (research G8, checked on 2026-10-30, above).

### Quoted for us

- entity class Algorithm: a method applied to data to compute a result, e.g. series of screens; modified nonlinear SST algorithm
- entity class SpatialExtent: an area the data cover, of the CelestialBody they are about: all of it (global) or part of it (e.g. Arctic; south pole of Mars; a country, when the data cover it)
- entity class CelestialBody: a natural object in space, or a kind of such objects, e.g. Vesta; active galactic nuclei
- predicate COMPUTED_FROM: was made by processing this input
- predicate PRODUCED_USING_ALGORITHM: was made or detected by applying this Algorithm
- predicate HAS_SPATIAL_COVERAGE: covers this SpatialExtent
- predicate HAS_TARGET: is about, or studies, this CelestialBody
- entity class PhysicalQuantity -> PhysicalQuantity: A measurable physical property or variable, such as temperature, wind speed, water vapor, or emission distribution, that is observed or derived in a dataset.
- predicate MEASURES -> HAS_MEASUREMENTS_OF: The subject (an instrument, mission, dataset or product) measures or provides data on the object, a physical quantity, variable or phenomenon.
- predicate PROVIDES -> HAS_MEASUREMENTS_OF: The subject (an instrument, data center, product or dataset) supplies or produces the object, a data product, measurement, variable or information layer.
- predicate MEASURED_BY -> HAS_MEASUREMENTS_OF (swap subject and object): Links a measured quantity to the instrument, system or method used to measure it.
- Writing a classed triple, rule 14: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 19: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 19: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.
- Writing a classed triple, rule 24: A processing step: output = method(input). For each processing step the record describes, find what it made (the output), what it was made from (the input), and how (the method). Each step gives up to two ground truth triples, each written only if the record names both of its ends

### Consequences

#### Option 1: Keep the line as the definitions draw it

- No change to the ground truth triples listed under Affects.
- The NDSI and the count rates stay Variables, though neither is a property of what is observed, and the current schema's PhysicalQuantity (in the translation table, quoted above for us) mixes the two ("a measurable physical property or variable"), so an extracted triple may use the other entity class.

#### Option 2: An entity class of its own for an index

- The ground truth triples with the NDSI change their entity class.
- One more entity class in the ground truth schema, for the annotation guidelines and the [model](../docs/terminology.md#8-the-pipeline) to tell apart from the other two.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 15: 32614a2f-a286-4c7c-9f1e-deafdf8bd6a3
- record at pool position 16: ec41fd5d-1159-4aa8-9803-5346e2324a20
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 22: 967275c7-aa2d-4b08-a9db-aff5cf6b7802
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_VARIABLE "Global Gravity" (Variable)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) COMPUTED_FROM "Normalized Difference Snow Index (NDSI)" (Variable)
- classed triple of the record at pool position 2: "Normalized Difference Snow Index (NDSI)" (Variable) COMPUTED_FROM "radiance data" (Dataset)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_MEASUREMENTS_OF "snow cover" (PhysicalQuantity)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_MEASUREMENTS_OF "Sea Surface Salinity (SSS) retrievals" (PhysicalQuantity)
- classed triple of the record at pool position 4: "skin SST" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "skin SST" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)
- classed triple of the record at pool position 4: "skin SST" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST" (Variable)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_MEASUREMENTS_OF "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VARIABLE "SST4" (Variable)
- classed triple of the record at pool position 4: "SST4" (Variable) LIMITED_BY "sun glint" (Phenomenon)
- classed triple of the record at pool position 4: "skin SST" (Variable) OBSERVED_AT_TIME_OF_DAY "day" (TimeOfDay)
- classed triple of the record at pool position 4: "skin SST" (Variable) OBSERVED_AT_TIME_OF_DAY "night" (TimeOfDay)
- classed triple of the record at pool position 4: "SST4" (Variable) OBSERVED_AT_TIME_OF_DAY "night" (TimeOfDay)
- classed triple of the record at pool position 4: "skin SST" (Variable) PRODUCED_USING_ALGORITHM "modified nonlinear SST algorithm" (Algorithm)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) COMPUTED_FROM "nominal fast neutron count rates" (Variable)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) HAS_VARIABLE "fast neutron residual count rates" (Variable)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) RELATED_TO "average atomic mass" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "atmospheric properties" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_ANCILLARY_DATA "view geometry" (Variable)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) PRODUCED_USING_ALGORITHM "Multi-Angle Implementation of Atmospheric Correction (MAIAC)" (Algorithm)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_MEASUREMENTS_OF "Land Surface Temperature" (PhysicalQuantity)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_MEASUREMENTS_OF "Land Surface Emissivity" (PhysicalQuantity)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "quality control assessments" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "observation times" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "view zenith angles" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "clear-sky coverages" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_VARIABLE "band 31 emissivity" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_VARIABLE "band 32 emissivity" (Variable)
- classed triple of the record at pool position 7: "band 31 emissivity" (Variable) COMPUTED_FROM "land cover types" (PhysicalQuantity)
- classed triple of the record at pool position 7: "band 32 emissivity" (Variable) COMPUTED_FROM "land cover types" (PhysicalQuantity)
- classed triple of the record at pool position 9: "RDR data" (Dataset) HAS_VARIABLE "dust fluences at each of twelve mass thresholds" (Variable)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_VARIABLE "Ensemble X-Ray Variability" (Variable)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_MEASUREMENTS_OF "redshifts" (PhysicalQuantity)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_MEASUREMENTS_OF "spectral classifications" (PhysicalQuantity)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_SPATIAL_REPRESENTATION "solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data" (SpatialRepresentation)
- classed triple of the record at pool position 15: "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data" (Dataset) HAS_MEASUREMENTS_OF "Heliocentric trajectories" (PhysicalQuantity)
- classed triple of the record at pool position 16: "PWS spectrum analyzer" (Instrument) MEASURES "spectral densities" (PhysicalQuantity)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) HAS_MEASUREMENTS_OF "counts" (PhysicalQuantity)
- classed triple of the record at pool position 19: "BARREL instrumentation" (Instrument) MEASURES "relativistic electron precipitation" (PhysicalQuantity)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_MEASUREMENTS_OF "surface water extent over land" (PhysicalQuantity)
- classed triple of the record at pool position 7: "band 31 emissivity" (Variable) FOR_CHANNEL "band 31" (Channel)
- classed triple of the record at pool position 7: "band 32 emissivity" (Variable) FOR_CHANNEL "band 32" (Channel)
- classed triple of the record at pool position 15: "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data" (Dataset) HAS_VARIABLE "Solar Orbiter Ephemeris" (Variable)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) HAS_VARIABLE "BRDF geometric parameter for VIIRS band M4 (0.555 μm)" (Variable)
- classed triple of the record at pool position 18: "BRDF geometric parameter for VIIRS band M4 (0.555 μm)" (Variable) FOR_CHANNEL "VIIRS band M4 (0.555 μm)" (Channel)
- classed triple of the record at pool position 18: "BRDF/Albedo values for VIIRS band M4" (Variable) COMPUTED_FROM "BRDF geometric parameter for VIIRS band M4 (0.555 μm)" (Variable)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) HAS_VARIABLE "NaI Scintillator Diagnostics" (Variable)
- classed triple of the record at pool position 22: "Flight Data For Tail 655" (Dataset) HAS_ANCILLARY_DATA "sampling rate" (Variable)
- classed triple of the record at pool position 22: "Flight Data For Tail 655" (Dataset) HAS_ANCILLARY_DATA "units" (Variable)
- classed triple of the record at pool position 22: "Flight Data For Tail 655" (Dataset) HAS_ANCILLARY_DATA "parameter description" (Variable)
- classed triple of the record at pool position 22: "Flight Data For Tail 655" (Dataset) HAS_ANCILLARY_DATA "parameter ID" (Variable)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_VARIABLE "Geopotential Height Zonal Fourier Coefficients" (Variable)
- classed triple of the record at pool position 24: "Geopotential Height Zonal Fourier Coefficients" (Variable) COMPUTED_FROM "HIRDLS profiles" (Dataset)
- classed triple of the record at pool position 24: "Geopotential Height Zonal Fourier Coefficients" (Variable) PRODUCED_USING_ALGORITHM "Kalman filter using both forward and backward passes in time" (Algorithm)
- classed triple of the record at pool position 24: "mean" (Variable) PART_OF "Geopotential Height Zonal Fourier Coefficients" (Variable)
- classed triple of the record at pool position 24: "Geopotential Height Zonal Fourier Coefficients" (Variable) HAS_NUMBER_OF "up to 7 sine coefficients" (Value)
- classed triple of the record at pool position 24: "Geopotential Height Zonal Fourier Coefficients" (Variable) HAS_NUMBER_OF "up to 7 cosine coefficients" (Value)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_ANCILLARY_DATA "precision values" (Variable)
- classed triple of the record at pool position 24: "precision values" (Variable) PRODUCED_USING_ALGORITHM "root-mean square" (Algorithm)
- classed triple of the record at pool position 24: "precision values" (Variable) COMPUTED_FROM "differences between the estimated fields and the input data" (Variable)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_VARIABLE "data field for ascending orbit node" (Variable)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_VARIABLE "data field for descending orbit node" (Variable)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_VARIABLE "data field for combined orbit node" (Variable)
- classed triple of the record at pool position 24: "data field for ascending orbit node" (Variable) OBSERVED_AT_TIME_OF_DAY "daytime" (TimeOfDay)
- classed triple of the record at pool position 24: "data field for descending orbit node" (Variable) OBSERVED_AT_TIME_OF_DAY "nighttime" (TimeOfDay)
- classed triple of the record at pool position 24: "data field for ascending orbit node" (Variable) HAS_NUMBER_OF "4 waves" (Value)
- classed triple of the record at pool position 24: "data field for descending orbit node" (Variable) HAS_NUMBER_OF "4 waves" (Value)
- classed triple of the record at pool position 24: "data field for combined orbit node" (Variable) HAS_NUMBER_OF "7 waves" (Value)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_VARIABLE "open inland water bodies greater than 3 hectares and 200 meters in width" (Variable)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_VARIABLE "water classification" (Variable)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_ANCILLARY_DATA "confidence" (Variable)
- translation table row: entity class PhysicalQuantity
- translation table row: predicate MEASURES
- translation table row: predicate PROVIDES
- translation table row: predicate MEASURED_BY
- ground truth schema entry: entity class PhysicalQuantity
- ground truth schema entry: entity class Variable
- ground truth schema entry: predicate HAS_MEASUREMENTS_OF
- ground truth schema entry: predicate HAS_VARIABLE
- ground truth schema entry: predicate ESTIMATES
- rule: Writing a classed triple, rule 14
- rule: Writing a classed triple, rule 19
- rule: Writing a classed triple, rule 24
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which follows any change to them

## Q4: Where a dataset's data come from: which relationships to tell apart, and what carries the instruments?

- status: open
- priority: high
- question kind: schema entry
- in short: the ground truth schema's FROM_MISSION, FROM_SPACECRAFT, ACQUIRED_BY_INSTRUMENT, HAS_MISSION_PHASE and OBTAINS_DATA_FROM, its Spacecraft, Mission and MissionPhase, and the translation table's rows for the current schema's SOURCED_FROM, platforms and campaigns

### The question

A record often says where its data came from: an instrument, the craft that carried it, a mission, a phase of a mission, a field campaign, or the data center that holds the data. Our schema has a separate predicate for several of these: a dataset is ACQUIRED_BY_INSTRUMENT an instrument, FROM_SPACECRAFT a spacecraft, FROM_MISSION a mission, and HAS_MISSION_PHASE a phase of a mission; a data center OBTAINS_DATA_FROM another organization (all defined below). Our Spacecraft is "a craft that operates in space", so it leaves out aircraft, balloons and ships. Other records of the catalog, which we have not annotated yet, name aircraft, balloons, the International Space Station, field campaigns and programs. We would like to know:

- (a) For a dataset of this catalog, which of these would someone in your field search for separately: the instrument, the craft that carried it, the mission, the phase of a mission, the field campaign, the data center? Which could be one relationship, "comes from", without losing anything you would search for? And does a record often state another source that is missing from this list?
- (c) Would someone in your field search for a dataset by the field campaign (a period of aircraft or balloon measurements) or the scientific program (for example, a telescope's legacy program) it comes from, apart from its mission?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: products from the Moderate-resolution Imaging Spectroradiometer (MODIS)
- source text: Aqua
- source text: JPL acquires MODIS ocean L3 SST data from the OBPG
- source text: The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple: "JPL" (Organization) OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" (Organization)

### Ground truth schema

- entity class Platform: a craft or station that carries Instruments, in space, in the air, on water or on the ground: a spacecraft, an aircraft, a balloon, a ship or a ground station, e.g. Aqua; Voyager 1
- entity class Mission: a named effort to collect data, from space, from the air, on water or on the ground, e.g. Rosetta; BARREL
- entity class MissionPhase: a named phase of a Mission
- predicate FROM_MISSION: was collected during this Mission
- predicate FROM_PLATFORM: was collected from this Platform
- predicate ACQUIRED_BY_INSTRUMENT: was collected by this Instrument
- predicate HAS_MISSION_PHASE: was collected during this MissionPhase
- predicate OBTAINS_DATA_FROM: receives data from

### Options

#### Option 1: Keep our entity classes and predicates as they are

Keep the predicates and entity classes above as they are: an aircraft, a campaign and a program have no entity class of their own, and a space station counts as a Spacecraft.

#### Option 2: One "comes from" predicate in the ground truth schema

Merge the predicates for the sources your answer to (a) says can be one.

#### Option 3: One entity class for anything that carries instruments

Widen Spacecraft (or put a new entity class, for example Platform, in its place) to any craft or station that carries instruments: satellites, aircraft, balloons, ships, space stations.

#### Option 4: Campaigns of their own

An entity class for a field campaign (for example, Campaign) and a predicate for data "collected during" a campaign, apart from a phase of a mission.

### My current reading

Keep the separate predicates (option 1 for them), unless your answer to (a) says some can be one (option 2): they follow what the records state. For the entity classes, option 3, decided on 2026-10-31: the ground truth schema's Platform now takes the place of Spacecraft, and FROM_PLATFORM of FROM_SPACECRAFT, since two records of batches 4 and 5 need it (a balloon, an aircraft) and the field has one "platform" for anything that carries instruments. Option 4 too, decided the same day: Campaign is an entity class of its own; your answer to (c) can still change both.

### My notes

Three [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070), "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0", "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" and "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", have ground truth that states several of these relationships; every classed triple the answer may change is listed under Affects. The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0". None of the records annotated so far (the first seven of the pool) names an aircraft, a balloon, a space station or a field campaign, so no ground truth triple shows them yet.

Changed on 2026-10-31: the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" no longer has "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument), left out by rule 1 of *What counts as a fact* (the record doesn't explain the code, so its entity class isn't written either), so that classed triple is no longer under Affects; the record's "Radio Science" is now "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) USES_TECHNIQUE "Radio Science" (Technique) (Q10).

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) now holds the old (a), (b) and (c); their (b) the old (d) and (e); their (c) the old (f) and (g). Two options were about our pipeline, not about the science, so we decide them ourselves once (a) is answered: the old options 2 and 3, below, with their consequences. The old options 4, 5 and 6 are now options 2, 3 and 4.

The question's opening, as it was: A record often says where its data came from: an instrument, the craft that carried it, a mission, a phase of a mission, a field campaign, or the data center that holds the data. The ground truth schema has one predicate for each of several of these (FROM_MISSION, FROM_SPACECRAFT, ACQUIRED_BY_INSTRUMENT, HAS_MISSION_PHASE, OBTAINS_DATA_FROM), and its Spacecraft is "a craft that operates in space", its Mission "a named spaceflight effort". The schema the [model](../docs/terminology.md#8-the-pipeline) extracts with, the current schema, learned from other records of the catalog, draws these lines differently: it has mostly one broad predicate for all of them, SOURCED_FROM, which the translation table translates to (none), nothing in the ground truth schema; its Spacecraft includes aircraft and balloons, and its Mission includes balloon programs. So a [fact](../docs/terminology.md#2-triples) of FROM_MISSION or FROM_SPACECRAFT, when the model extracts it under SOURCED_FROM, can't count as found, and the same aircraft counts differently depending on which word of the current schema the model used.

- (a) For a dataset of this catalog, which of these are different relationships that someone in your field would ask about separately: the instrument, the craft that carried it (a spacecraft, or an aircraft, ship, balloon, ground station), the mission, the phase of a mission, the field campaign, the data center?
- (b) Which of them could be one relationship, "comes from", without losing anything you would search for?
- (c) Are there others a record of this catalog often states that are missing from that list?
- (d) Is an aircraft or a balloon that carries instruments the same kind of thing as a spacecraft, for this catalog (a "platform" in Earth science)? Should the ground truth schema have one entity class for anything that carries instruments, or keep spacecraft apart?
- (e) Is a space station (the International Space Station) a spacecraft?
- (f) Is a field campaign (a period of aircraft or balloon measurements) a phase of a mission, a mission of its own, or something else?
- (g) Is a scientific program (for example, a telescope's legacy program) a mission?

The question's context, as it was: The example below names an instrument, the spacecraft that carries it, and a data center. In the current schema, the model filed such facts under SOURCED_FROM, ACQUIRED_BY and COLLECTED_DURING (the translation table's [rows](../docs/terminology.md#8-the-pipeline) for them are below). The example also says that the data center, JPL, "acquires MODIS ocean L3 SST data from the OBPG", which the ground truth writes with OBTAINS_DATA_FROM.

None of the records we have read so far names an aircraft, a balloon, a space station or a field campaign; they come up in records the model read when it learned the current schema. Before the model's classed triples are compared with the ground truth, each entity class and predicate of the current schema is translated into the one of the ground truth schema its row of the translation table names; a row that names (none) means the model's classed triples with it count as not in the ground truth.

The options as they were, before 2026-10-26:

- Option 1: Keep the ground truth schema and the translation table as they are. SOURCED_FROM, an aircraft, a campaign and a program (current schema) translate to (none); a space station to Spacecraft; the current schema's Spacecraft and Mission to the ground truth schema's Spacecraft and Mission; "collected during" to HAS_MISSION_PHASE.
- Option 2: Translate SOURCED_FROM by the entity class of its object. A row of the translation table could say: SOURCED_FROM (current schema) with a Mission as object instance translates to FROM_MISSION (ground truth schema), with a Spacecraft to FROM_SPACECRAFT, and with anything else to (none). Today a row translates a predicate one way only, whatever its object. Its consequences: the ground truth stays as it is; the change is in how the extracted triples are compared with it ([step](../docs/terminology.md#8-the-pipeline) 070 and the translation table's format). It works only for the relationships that differ by the object's entity class; two that share one (a campaign and a mission, if both are Missions) stay mixed.
- Option 3: Let the current schema split SOURCED_FROM into one predicate per sense. When the current schema is learned (step 040), a broad predicate whose object instances are of several entity classes is split into one predicate per entity class, each of which the translation table can translate on its own. Its consequences: the model extracts with the separate predicates, so the facts can count as found. A few more predicates in the current schema, so a longer schema in every request to the model; steps 040, 060 and 070 run again.
- Option 4: One "comes from" predicate in the ground truth schema. Merge the ground truth schema's predicates for the senses your answer to (b) says can be one.
- Option 5: One entity class for anything that carries instruments. The ground truth schema's Spacecraft is widened (or a new entity class, for example Platform, takes its place) to any craft or station that carries instruments: satellites, aircraft, balloons, ships, space stations.
- Option 6: Campaigns of their own. Coin an entity class for a field campaign (for example, Campaign) and a predicate for "collected during" a campaign, apart from MissionPhase.

My current reading, as it was: Options 2 to 4 are about the predicates, options 5 and 6 about the entity classes, so one of each can be combined. For the predicates, option 3, then option 2 for what it leaves mixed: they keep the ground truth schema's distinctions, which follow what the records state, and fix the cause in the current schema, while option 4 throws the distinctions away. Your answers to (a) and (b) tell us which distinctions are worth keeping. For the entity classes, undecided: option 5 looks closer to how Earth science data are described, but no record annotated so far needs it, nor option 6; your answers to (d) and (f) decide them.

Taken out of the expert's view on 2026-10-31, as settled from the field's practice (the research of 2026-10-31); kept here word for word: "- (b) Is an aircraft, a balloon, a ship or a space station that carries instruments the same kind of thing as a spacecraft, for this catalog (a "platform" in Earth science)? Should we have one entity class for anything that carries instruments, or keep spacecraft apart?" My current reading ended: "For the entity classes, undecided: option 3 looks closer to how Earth science data are described, but no record we have annotated needs it, nor option 4; your answers to (b) and (c) decide them."

Checked on 2026-10-31, the old (b): the field has one kind of thing for anything that carries instruments, a platform. W3C SOSA: "A Platform is an entity [a thing] that hosts other entities [things], particularly Sensors, Actuators, Samplers, and other Platforms", and "A post, buoy, vehicle, ship, aircraft, satellite, cell-phone, human or animal may act as Platforms" (https://www.w3.org/TR/vocab-ssn/); NASA's GCMD Platforms keywords (version 25.1) group them as Space-based, Air-based, Water-based and Land-based platforms, with space stations and crewed spacecraft among the Space-based ones (https://gcmd.earthdata.nasa.gov/KeywordViewer/); NASA's metadata standard UMM-C: "The controlled vocabulary for platform types … includes Spacecraft, Aircraft, Vessel, Buoy, Platform, Station, Network, Human, etc.". Whether our schema gets one entity class for it (option 3), with Spacecraft as a kind of it (Q25), is ours to decide once a record needs it: docs/improvements.md, *An entity class hierarchy for the schemas*, after the first run.

Checked on 2026-10-31, for the expert's (a): NASA's own search keeps these apart. Earthdata Search's filters are "Features, Keywords, Platforms, Instruments, Organizations, Projects, Processing levels", among others (MAAP's guide to Earthdata Search, https://docs.maap-project.org/en/hub/technical_tutorials/search/searching_edsc_gui.html; strong secondary), and UMM-C keeps Platforms, Instruments, Projects ("The name of the scientific program, field campaign, or project from which the data were collected.") and DataCenters as fields of their own. No filter covers a mission phase. That supports keeping the predicates apart (option 1); the expert's (a) still asks about mission phases and anything else people search for.

Checked on 2026-10-31, for the expert's (a), the data center's part (the research of 2026-10-31 on NASA's metadata): UMM-C's DataCenters carry a closed list of roles, ARCHIVER, DISTRIBUTOR, PROCESSOR and ORIGINATOR (`DataCenterRoleEnum`). CMR's record of the example product (C2036881966-POCLOUD) lists the platform Aqua carrying MODIS, the project EOS, and the data centers OBPG (PROCESSOR) and NASA/JPL/PODAAC (ARCHIVER). So the field keeps the four apart, and the roles map onto our predicates: OBPG as PROCESSOR fits DEVELOPED_BY_PARTY, PO.DAAC as ARCHIVER the archive JPL is. This informs option 1; the record's words decide each triple.

Checked on 2026-10-31, the old (b), in two more vocabularies: PDS4's Instrument_Host type must be one of "'Aircraft', 'Balloon', 'Earth Based', 'Earth-based', 'Lander', 'Rover', 'Spacecraft', 'Suborbital Rocket'" (the PDS4 schematron, IM 1.23.0.0, https://pds.nasa.gov/datastandards/schema/released/pds/v1/PDS4_PDS_1N00.sch), and SPASE's Observatory is "The host (spacecraft, network, facility) for instruments making observations, or a family of closely related hosts" (SPASE 2.7.1, https://spase-group.org/data/model/spase-2.7.1.pdf). So all four vocabularies (GCMD, PDS4, SPASE, SOSA) have one kind of thing for whatever carries instruments, with the kinds below it. If a Platform entity class is coined, PDS4's type list and GCMD's platform categories could give its subclasses (docs/improvements.md, *Linking subject instances and object instances to reference lists*, 080). No ground truth triple changes: no annotated record names a carrier that is not a spacecraft.

Checked on 2026-10-31, the old (c): neither of NASA's vocabularies makes a field campaign a phase of a mission. PDS4 files a field campaign and an observing campaign as kinds of investigation beside a mission: "The attribute pds:Investigation/pds:type must be equal to one of the following values 'Field Campaign', 'Individual Investigation', 'Mission', 'Observing Campaign', 'Other Investigation'", an Investigation being "A set of experiments and/or observations with a clearly defined purpose" (the PDS4 schematron and schema, IM 1.23.0.0). UMM-C files campaigns under a project, "The name of the scientific program, field campaign, or project from which the data were collected", and "Project also includes the Campaign sub-element to support multiple campaigns under the same project". So a campaign is a sibling of a mission (PDS4) or a part of a project (UMM-C), and a long program is a project (UMM-C) or another kind of investigation (PDS4). That supports option 4, or one entity class for an investigation with Mission as one kind of it; the choice is ours. Taken out of the expert's view on 2026-10-31, as settled from these sources (B14's pattern); kept here word for word: "- (c) Is a field campaign (a period of aircraft or balloon measurements) a phase of a mission, a mission of its own, or something else? And is a scientific program (for example, a telescope's legacy program) a mission?" The expert's (c) now asks only whether people search by campaign or program.

### Quoted for us

- predicate DEVELOPED_BY_PARTY: was built or created by this Person or Organization
- predicate SOURCED_FROM -> (none): The subject (a dataset, file, objective or person) originates from the object, a source instrument, platform, observation set, data portion or institution.
- predicate ACQUIRED_BY -> ACQUIRED_BY_INSTRUMENT: The subject (a dataset or observed class of objects) is collected or detected by the object, an instrument or platform.
- predicate COLLECTED_DURING -> HAS_MISSION_PHASE: The subject (a dataset, campaign, mission activity or event) took place or was gathered during the object, a time period or named field campaign.
- predicate PROVIDED_BY -> PROVIDED_BY_PARTY: The subject (a product, campaign or responsibility) is supplied, conducted or overseen by the object, an organization, team or instrument mission.
- entity class Spacecraft -> Platform: A vehicle or platform, such as a satellite, aircraft, or balloon, that carries instruments to collect observations.
- entity class SpaceStation -> Platform: A crewed orbiting space station, such as the International Space Station, used as a platform for research and observation.
- entity class Aircraft -> (none): A crewed or research airplane used as a platform for airborne observations or measurements.
- entity class Mission -> Mission: A planned space or flight undertaking, such as a satellite mission, balloon program, or spaceflight of a given duration, carried out to accomplish scientific objectives.
- entity class Campaign -> (none): A coordinated period of field or flight measurement activity, such as an aircraft or balloon campaign, conducted to collect data.
- entity class Program -> (none): A named organized scientific initiative, often a telescope legacy or key program, encompassing coordinated observations and data products.
- Writing a classed triple, rule 14: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 15: One fact per ground truth triple. A sentence that states two facts gives two ground truth triples.

### Consequences

#### Option 1: Keep our entity classes and predicates as they are

- Nothing changes.
- Facts the model extracts under SOURCED_FROM never count as found (unless we take the old option 2 or 3, in My notes).
- An aircraft that the current schema calls a Spacecraft is compared with the ground truth's Spacecraft, while one it calls an Aircraft is left out.
- A dataset "collected during" a field campaign is compared with HAS_MISSION_PHASE, though a campaign isn't a phase of a spaceflight effort.

#### Option 2: One "comes from" predicate in the ground truth schema

- The ground truth triples listed under Affects that use those predicates change, and the ground truth schema loses the difference between them.
- Extraction and the ground truth agree more easily, but a search for "all data from the Aqua spacecraft" can no longer be told from "all data of the Aqua mission".

#### Option 3: One entity class for anything that carries instruments

- The rows for Aircraft and SpaceStation (current schema) translate to it; FROM_SPACECRAFT is renamed or widened with it.
- The annotation guidelines and the ground truth triples with Spacecraft are checked again.

#### Option 4: Campaigns of their own

- The rows for Campaign and COLLECTED_DURING (current schema) translate to them.
- A new entity class and predicate in the ground truth schema, used by no tuning record yet.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 10: 3bceffb4-f01e-433c-af79-42b9d9427231
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 16: ec41fd5d-1159-4aa8-9803-5346e2324a20
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- record at pool position 22: 967275c7-aa2d-4b08-a9db-aff5cf6b7802
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- record at pool position 21: 264a9b23-9a86-46a7-ab61-9661230ea667
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_PLATFORM "ROSETTA-ORBITER" (Platform)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_MISSION_PHASE "COMET ESCORT 4" (MissionPhase)
- classed triple of the record at pool position 1: "COMET ESCORT 4" (MissionPhase) HAS_TIME_SPAN "2015-10-22 to 2015-12-31" (Time)
- classed triple of the record at pool position 2: "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Platform)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "radiance data" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) ACQUIRED_BY_INSTRUMENT "Aquarius L-band radiometer" (Instrument)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) FROM_MISSION "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission)
- classed triple of the record at pool position 4: "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Platform)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 4: "Aqua" (Platform) FLIES_IN "A-train" (SatelliteFormation)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the atmosphere" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the land" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the oceans" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_TARGET "Earth" (CelestialBody)
- classed triple of the record at pool position 4: "Aqua" (Platform) LAUNCHED_BY_PARTY "NASA" (Organization)
- classed triple of the record at pool position 4: "Aqua" (Platform) LAUNCHED_ON "May 4, 2002" (Time)
- classed triple of the record at pool position 4: "JPL" (Organization) OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- classed triple of the record at pool position 5: "GRaND epithermal neutron map" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND plus Z boron loaded sensor" (Instrument)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) FROM_PLATFORM "DAWN" (Platform)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_PLATFORM "Terra" (Platform)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) FROM_PLATFORM "Terra" (Platform)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) ACQUIRED_BY_INSTRUMENT "MODIS" (Instrument)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) FROM_PLATFORM "STARDUST" (Platform)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) FROM_MISSION "Stardust-NExT" (Mission)
- classed triple of the record at pool position 9: "Stardust-NExT" (Mission) ENDED_ON "March, 2011" (Time)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) HAS_MISSION_PHASE "cruise" (MissionPhase)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) HAS_MISSION_PHASE "approach" (MissionPhase)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) HAS_MISSION_PHASE "encounter" (MissionPhase)
- classed triple of the record at pool position 9: "RDR data" (Dataset) HAS_MISSION_PHASE "encounter" (MissionPhase)
- classed triple of the record at pool position 9: "approach" (MissionPhase) HAS_TARGET "9P/Tempel 1" (CelestialBody)
- classed triple of the record at pool position 9: "encounter" (MissionPhase) HAS_TARGET "9P/Tempel 1" (CelestialBody)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Dust Flux Monitor Instrument (DFMI)" (Instrument)
- classed triple of the record at pool position 10: "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (Dataset) FROM_PLATFORM "Rosetta Orbiter" (Platform)
- classed triple of the record at pool position 10: "Rosetta Orbiter ALICE UV Spectrometer" (Instrument) ABOARD "Rosetta Orbiter" (Platform)
- classed triple of the record at pool position 10: "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (Dataset) HAS_MISSION_PHASE "comet escort 1" (MissionPhase)
- classed triple of the record at pool position 10: "comet escort 1" (MissionPhase) HAS_TIME_SPAN "between 2014-11-19 and 2015-03-10" (Time)
- classed triple of the record at pool position 10: "comet escort 1" (MissionPhase) HAS_TARGET "67P/Churyumov-Gerasimenko" (CelestialBody)
- classed triple of the record at pool position 10: "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Rosetta Orbiter ALICE UV Spectrometer" (Instrument)
- classed triple of the record at pool position 12: "2XMMi-DR3" (Dataset) FROM_PLATFORM "XMM-Newton" (Platform)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) FROM_PLATFORM "XMM-Newton" (Platform)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) FROM_PLATFORM "ROSETTA-ORBITER" (Platform)
- classed triple of the record at pool position 13: "OSIRIS Narrow Angle Camera" (Instrument) ABOARD "ROSETTA-ORBITER" (Platform)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_MISSION_PHASE "COMET ESCORT 3" (MissionPhase)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "OSIRIS Narrow Angle Camera" (Instrument)
- classed triple of the record at pool position 4: "Aqua" (Platform) FLIES_IN "Earth Observation Satellites (EOS)" (SatelliteFormation)
- classed triple of the record at pool position 16: "Plasma Wave Spectrometer (PWS)" (Instrument) ABOARD "Voyager 1" (Platform)
- classed triple of the record at pool position 16: "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (Dataset) FROM_PLATFORM "Voyager 1" (Platform)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) FROM_PLATFORM "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)" (Platform)
- classed triple of the record at pool position 19: "X-ray spectrometer" (Instrument) ABOARD "BARREL balloon" (Platform)
- classed triple of the record at pool position 19: "DC magnetometer" (Instrument) ABOARD "BARREL balloon" (Platform)
- classed triple of the record at pool position 19: "BARREL balloon" (Platform) HAS_MASS "approximately 20 kg" (Value)
- classed triple of the record at pool position 22: "Flight Data For Tail 655" (Dataset) FROM_PLATFORM "Tail 655" (Platform)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) FROM_PLATFORM "Aura" (Platform)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) FROM_PLATFORM "Sentinel-1" (Platform)
- classed triple of the record at pool position 25: "Sentinel-1 radar observations" (Dataset) FROM_PLATFORM "Sentinel-1" (Platform)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) FROM_MISSION "BARREL" (Mission)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "study electron losses from Radiation Belts" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_TARGET "Earth" (CelestialBody)
- classed triple of the record at pool position 19: "BARREL" (Mission) PART_OF "NASA Living with a Star" (Organization)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "augment the Radiation Belt Storm Probes, RBSP, mission" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "providing measurements of the spatial variations of electron precipitation from the radiation belts" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "providing measurements of the temporal variations of electron precipitation from the radiation belts" (Purpose)
- classed triple of the record at pool position 19: "Radiation Belt Storm Probes, RBSP" (Mission) ALSO_KNOWN_AS "Van Allen Probes" (Mission)
- classed triple of the record at pool position 19: "August 2015 BARREL campaign" (Campaign) COORDINATED_WITH "Radiation Belt Storm Probes, RBSP" (Mission)
- classed triple of the record at pool position 19: "2016 campaign" (Campaign) COORDINATED_WITH "Radiation Belt Storm Probes, RBSP" (Mission)
- classed triple of the record at pool position 19: "2013 balloon campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "2014 balloon campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "August 2015 BARREL campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "2016 campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_NUMBER_OF "four BARREL campaigns" (Value)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_NUMBER_OF "over 50 small, approximately 20 kg, stratospheric balloons" (Value)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_TIME_SPAN "from 2013 to 2016" (Time)
- classed triple of the record at pool position 21: "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (Dataset) FROM_MISSION "Chandrayaan-1" (Mission)
- classed triple of the record at pool position 21: "Chandrayaan-1" (Mission) HAS_TARGET "Moon" (CelestialBody)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument)
- classed triple of the record at pool position 16: "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "PWS spectrum analyzer" (Instrument)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) ACQUIRED_BY_INSTRUMENT "Visible Infrared Imaging Radiometer Suite (VIIRS)" (Instrument)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) ACQUIRED_BY_INSTRUMENT "Rate Counter (RCNT)" (Instrument)
- classed triple of the record at pool position 21: "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Moon Mineralogy Mapper (M3)" (Instrument)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) ACQUIRED_BY_INSTRUMENT "HIRDLS" (Instrument)
- classed triple of the record at pool position 24: "HIRDLS profiles" (Dataset) ACQUIRED_BY_INSTRUMENT "HIRDLS" (Instrument)
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
- translation table row: predicate OBSERVED_BY
- ground truth schema entry: entity class Platform
- ground truth schema entry: entity class Mission
- ground truth schema entry: entity class MissionPhase
- ground truth schema entry: predicate FROM_MISSION
- ground truth schema entry: predicate FROM_PLATFORM
- ground truth schema entry: predicate ACQUIRED_BY_INSTRUMENT
- ground truth schema entry: predicate HAS_MISSION_PHASE
- ground truth schema entry: predicate OBTAINS_DATA_FROM
- rule: Writing a classed triple, rule 14
- rule: Writing a classed triple, rule 15
- pipeline method: 040_induce_schema/run.py: how the current schema is learned (the old option 3, in My notes: splitting a broad predicate)
- pipeline method: common/common_helpers/component_class_mapping.py: how a row of the translation table translates (the old option 2, in My notes: by the entity class of the object)

## Q5: Time in a record: temporal resolution, the time a file covers, and the period a dataset covers

- status: open
- priority: high
- question kind: schema entry
- in short: the ground truth schema's TemporalResolution, Time and Value, its HAS_TEMPORAL_RESOLUTION, HAS_GRANULE_DURATION and HAS_TIME_SPAN, and the translation table's rows for the current schema's Frequency, HAS_TIME_RESOLUTION, COVERS and HAS_DURATION

### The question

Records state time in several ways, and our schema has a predicate for each kind we have met (all defined below): how often the data give a value, its temporal resolution ("daily"); how much time each file covers ("5 minutes"); how long a set of observations lasts ("a ~40 minute period"); and the period on the calendar the data cover ("2015-11-01T19:58:35.000 to 2015-11-02T04:59:27.000"). Some records' words fit more than one of these. We would like to know:

- (a) What is a dataset's temporal resolution? The example below is a swath dataset whose files each hold "5 minutes of swath data", and it "provides daily snow cover". Is "daily" the time between one value and the next? Our reading, not checked against a source: each file holds what the instrument saw along its path in those 5 minutes, and "daily" says how often the product is made, or how often the instrument passes over the same ground. What your answer can still change: whether this record's "daily" is a temporal resolution at all (option 3); and, for the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" ("produced daily"), whose daily files hold one value per pass of the satellite, several a day near the poles, whether "daily" is the time between values or the time each file covers.
- (b) Would someone searching this catalog want these kept apart: the time each file covers, how long a set of observations lasts (the record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0", whose Tempel 1 encounter data cover "a ~40 minute period"), and the period on the calendar? And is a granule, in this catalog, always one file?

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

- entity class TemporalResolution: an amount of time between one value of the data and the next, e.g. daily; weekly (8 day)
- entity class Time: a point or period on the calendar, which happens once, e.g. March 11, 2016 19:08:03; May 4, 2002; first week of February 2003; 2015-10-22 to 2015-12-31
- entity class Value: an amount, or a range of amounts, as a number with its unit or in words, e.g. 36 spectral bands; 5 minutes
- predicate HAS_TEMPORAL_RESOLUTION: its values are this far apart in time, e.g. daily
- predicate HAS_GRANULE_DURATION: each of its files covers this much time
- predicate HAS_DURATION: covers this much time, from its first value to its last
- predicate HAS_TIME_SPAN: covers this period

### Options

#### Option 1: Keep our entity classes and predicates as they are

Any word that says how often values come, or the period they average over ("daily", "weekly", "weekly (8 day)"), is a temporal resolution, in the record's own words.

#### Option 2: Tell apart how often from the period a value averages over

A temporal resolution only for the time between one value and the next; a new entity class, and a new predicate, for the period one value averages over ("8 day" in an 8-day average).

#### Option 3: No temporal resolution for a swath dataset

Where the dataset's files hold what the instrument saw along its path, "daily" is not a temporal resolution; it would be a different relationship ("is made daily"), or none.

### My current reading

Option 1 for now, because the definition of a temporal resolution covers the records we have read so far as they are written and needs no knowledge from outside the record. If your answer to (a) is that "daily" means something else for a swath dataset, we would move to option 3 for those datasets; if the averaging period is a separate thing, to option 2. Your answer to (b) tells us whether the three predicates for amounts and periods of time are the right ones.

### My notes

Five of the [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) we have annotated so far state a time of these sorts: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0", "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061", "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005", "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" and "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (the last is in the ground truth now); every classed triple the answer may change is listed under Affects. The example is the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061"; the "8 Day" one is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", the period one the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0".

Option 4 comes when we improve the step that learns the schema (040): splitting a broad predicate by its object's entity class is on our list of improvements.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) now holds the old (a) and (b); their (b) the old (c), (d), (e) and (h). The old (f) and (g) are about how the current schema mixes meanings (COVERS, Frequency); our reading answers them (a period and an area never share a predicate in the ground truth schema; a radio band is not a temporal resolution), so we settle them ourselves with the old option 4, below. The old options 1 to 3 kept their numbers; option 1's title and text no longer name the translation table.

The question's opening, as it was: The ground truth schema has three entity classes for time: Time, "a point or period on the calendar, which happens once"; TemporalResolution, "the amount of time between one value of the data and the next, e.g. daily; weekly (8 day)"; and Value, "an amount", which HAS_GRANULE_DURATION uses for how much time each file covers. Its predicates for time are HAS_TEMPORAL_RESOLUTION ("gives values this often"), HAS_GRANULE_DURATION ("each of its files covers this much time") and HAS_TIME_SPAN ("covers this period"). Some records' words for time fit more than one of them, and the schema the [model](../docs/terminology.md#8-the-pipeline) extracts with, the current schema, learned from other records of the catalog, draws the lines more widely (its entries are in the translation table, below).

- (a) The record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061", the example below, is a Level-2 swath dataset whose files each hold "5 minutes of swath data", and the record says it "provides daily snow cover". Is "daily" its temporal resolution, the time between one value and the next? Our reading, not checked against a source: each file holds what the instrument saw along its path in those 5 minutes, and "daily" says how often the product is made, or how often the instrument passes over the same ground, not the time between two values in a file.
- (b) The record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" is an "8 Day" average ("Average daily, weekly (8 day), monthly and annual skin SST products"). Its 8 days are both the time each value averages over and the time between one value and the next. Is that one thing, a temporal resolution, or two that should be told apart (the period a value averages over, and how often a value is given)?
- (c) Is the line between Time (a date or period that happens once), TemporalResolution (how often), and the time a file covers (HAS_GRANULE_DURATION, a Value) the one you would draw?
- (d) Is a granule, for this catalog, always one file? The ground truth schema's HAS_GRANULE_DURATION says "each of its files", reading the example below that way.
- (e) Is "each file (granule) covers 5 minutes" the same kind of fact as "the observation series lasted 3 years"? Would someone searching this catalog want them kept apart?
- (f) In this catalog, when a record says a dataset "covers" something, is it more often a period, an area, or a measured variable? Should "covers the Arctic" and "covers 2003 to 2010" ever share one predicate?
- (g) The current schema's entity class Frequency puts two things together: "A rate of occurrence, such as daily or weekly, or a radio frequency band, such as S-, X-, or Ku-band", and the translation table translates it into TemporalResolution. In this catalog, are how often data are given (daily, weekly) and a radio frequency band (S-band, X-band, Ku-band) two different kinds of thing, which should never share an entity class? (Our reading is that they are: one is a time between values, the other a part of the radio spectrum. Where a radio band belongs, we ask separately.)
- (h) The record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" says its data run "from January, 2007, through cruise, approach to and encounter with comet 9P/Tempel 1, and up to end of mission in March, 2011", and that its encounter data cover "a ~40 minute period". We wrote the period as "January, 2007 up to March, 2011" (Time), its two ends in the record's words with the phases taken out (they are facts of their own), and the 40 minutes with a predicate we coined, HAS_DURATION ("covers this much time, from its first value to its last"): "encounter data" (Dataset) HAS_DURATION "~40 minute period" (Value). Is how long a set of observations lasts a fact to keep apart from the period on the calendar, and from the time a file covers (question (e))?

The question's context, as it was: The example below states both how often ("daily") and how much time each file covers ("5 minutes"). Under rule 19 of *Writing a classed triple* (quoted below), a word such as "daily" in "daily snow cover" is taken out of the object instance and written as a temporal resolution of its own.

We write these facts with different predicates of the ground truth schema: HAS_TIME_SPAN for a period (the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0": "covers the time 2015-11-01T19:58:35.000 to 2015-11-02T04:59:27.000"), HAS_SPATIAL_COVERAGE for an area, and HAS_GRANULE_DURATION for the time each file covers (the example below). Before the model's classed triples are compared with the ground truth, each entity class and predicate of the current schema is translated into the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names, and a row names only one. So a classed triple of the model that uses COVERS for an area is compared as a period, and one that files a radio band under Frequency is compared as a temporal resolution: both are counted wrong even when the model found the fact.

The options as they were, before 2026-10-26:

- Option 1: Keep the ground truth schema and the translation table as they are. Any word that says how often values come, or the period they average over ("daily", "weekly", "weekly (8 day)"), is a TemporalResolution, in the record's own words; the rows stay: Frequency into TemporalResolution, COVERS into HAS_TIME_SPAN, HAS_DURATION into HAS_GRANULE_DURATION.
- Option 4: Let the current schema keep the meanings apart. The [step](../docs/terminology.md#8-the-pipeline) that learns the current schema splits a predicate whose object instances are of several entity classes into one predicate per entity class (COVERS with a period; COVERS with an area), and keeps how often data are given apart from a radio frequency band; each part gets its own row: into HAS_TIME_SPAN, into HAS_SPATIAL_COVERAGE, into TemporalResolution. Its consequences: each meaning is compared with the right ground truth predicate or entity class. The learning step changes, and its next run costs model calls; the new rows are checked by hand. It doesn't settle (e): whether a whole series' duration needs a predicate of its own in the ground truth schema.

My current reading, as it was: Option 1 for now, because the definition of TemporalResolution covers the records we have read so far as they are written and needs no knowledge from outside the record; and option 4 later. If your answer to (a) is that "daily" means something else for a swath dataset, we would move to option 3 for those datasets; if your answer to (b) is that the averaging period is a separate thing, to option 2. Your answer to (e) decides whether the ground truth schema also needs a predicate for how long a whole series lasted.

Taken out of the expert's view on 2026-10-31, as settled from a source; kept here word for word, the end of (a): "And in an "8 Day" average (the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0": "Average daily, weekly (8 day), monthly and annual skin SST products"), the 8 days are both the time each value averages over and the time between two values: one thing, or two to tell apart?" Checked on 2026-10-30 (research M12): an OBPG "8 Day" Level 3 value is the mean of all Level 2 data in a fixed, contiguous 8-day period, so the 8 days are both the time each value averages over and the time between two values, one thing for such a product; option 2 would be needed only for rolling composites (e.g. OBPG's Rolling 32-Day), and no tuning record has one. Decided on 2026-10-31: the record's "Average" is now a ground truth triple of its own, the method, beside its temporal resolution: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) PRODUCED_USING_ALGORITHM "Average" (Algorithm) (rule 24 of *Writing a classed triple*; source text "Average daily, weekly (8 day)"). Added on 2026-10-31, from the third audit (finding G-11): the expert's (c), a reading question; the ground truth triple stays as it is until it is answered.

Taken out of the expert's view on 2026-10-31, as settled from a source (the research of 2026-10-31); kept here word for word: "- (c) The record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" says "The RDR data convert the EDR (raw) sensor data, from the entire comet encounter, to dust fluences at each of twelve mass thresholds". We wrote that the RDR data come from the encounter ("RDR data" (Dataset) HAS_MISSION_PHASE "encounter" (MissionPhase)). Read with its commas, "from the entire comet encounter" may describe only the EDR (raw) sensor data, which the RDR data are made from. Which data does it describe?"

Checked on 2026-10-31, the old (c): the data set's own catalog file (https://pdssbn.astro.umd.edu/holdings/sdu-c_d-dfmi-2_3-next-tempel1-v1.0/catalog/) says "In the RDR data, each row represents an accumulated fluence for the duration of the Tempel 1 encounter for one threshold. There are no RDR data corresponding to the non-ENCOUNTER CRUISE mode EDR data." So the RDR data come only from the encounter, and "RDR data" (Dataset) HAS_MISSION_PHASE "encounter" (MissionPhase) is true on either reading; it stays. "entire" fits the EDR (raw) data better: "RDR ENCOUNTER data contain fluences (cumulative impacts) for the duration of the encounter up to before the start of the anomaly", about 27 minutes into the encounter's "~40 minutes" (my reading, from these facts; the anomaly's time is for 080's enrichment, since the record doesn't state it). "entire" stays left out by rule 9 of *What counts as a fact* (annotations/left_out.md).

Added on 2026-10-31, for the expert's (a) (the research of 2026-10-31): the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" fits our definition exactly: "In the C6 MOD11A1 product, LST values at all grids are from single clear-sky MODIS observations" (MOD11 user guide, section 3.1, https://modis-land.gsfc.nasa.gov/pdf/MOD11_User_Guide_V61.pdf), at most one value per cell a day, and NASA's metadata gives "1 Day"; so does the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" ("the temporal resolution of the product was set to one week, corresponding to the time of revisit", NSIDC's user guide, section 3.2). The record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" does not: "The current dataset presents data per orbit", and "Each daily file (MCD19A1 and A2) usually contains multiple orbit overpasses (1-2 at equator and up to 30 in polar regions for combined Terra and Aqua)" (MAIAC user guide, section 3.1, https://lpdaac.usgs.gov/documents/1500/MCD19_User_Guide_V61.pdf), while NASA's metadata gives it "1 Day". NASA's metadata uses "temporal resolution" loosely (5 minutes, one granule, for the swath record), so it is not reliably the time between one value and the next. The record's words stand either way (rule 1 of *What counts as a fact*); the expert's (a) now says what an answer can still change (the inventory of 2026-10-31, as research B14 narrowed other questions). For the expert's (b): W3C DCAT keeps a dataset's temporal resolution ("Minimum time period resolvable in the dataset"), its temporal coverage and how often it is published apart (https://www.w3.org/TR/vocab-dcat-3/), and NASA's UMM-C keeps TemporalExtents apart from the temporal resolution; neither has a collection-level field for the time each file covers, which NASA keeps per granule.

### Quoted for us

- predicate HAS_SPATIAL_COVERAGE: covers this SpatialExtent
- entity class Frequency -> TemporalResolution: A rate of occurrence, such as daily or weekly, or a radio frequency band, such as S-, X-, or Ku-band.
- predicate HAS_TIME_RESOLUTION -> HAS_TEMPORAL_RESOLUTION: The subject (a dataset or measurement) has the object as its temporal resolution, averaging interval, cycle or file time-period.
- predicate COVERS -> HAS_TIME_SPAN: The subject (a dataset, campaign, flight series or technique) spans the object, a time period, geographic area or measured variable.
- predicate HAS_DURATION -> HAS_GRANULE_DURATION: The subject (a dataset, granule, orbit portion or observation series) lasts for or spans the object, a time length or period.
- Writing a classed triple, rule 19: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 21: General facts: include them; about another dataset, only when the record links it to the record's dataset by "part of" or "made from".
- Writing a classed triple, rule 21: Another dataset. Include facts about another dataset when the record states a chain of "part of" or "made from" links that connects it to the record's dataset: its parts, what it is part of, what it is made from, and so on through further datasets or variables the record names. Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it. In every case, include the connection the record states (rule 1 of What counts as a fact: only what the record states).
- Writing a classed triple, rule 21: Suppose: a record's title says "8 Day", and its notes say "daily, weekly (8 day), and monthly products are available from this instrument's output". Then: the record's dataset HAS_TEMPORAL_RESOLUTION "weekly (8 day)", its own (by rule 23, it says more than "8 Day"); the daily and monthly products are variants of the record's dataset, and the record states no connection beyond that, so they get none.

### Consequences

#### Option 1: Keep our entity classes and predicates as they are

- No change to the ground truth triples listed under Affects.
- "daily" for a dataset of 5-minute swath files and "daily" for a dataset with one value per place per day look the same, though they may mean different things (the expert's answer to (a)).
- Until the old option 4 (in My notes) is done, an area or a variable the model writes with COVERS, a whole series' duration written with HAS_DURATION, and a radio band filed under Frequency are compared with the wrong ground truth predicate or entity class, and counted wrong.

#### Option 2: Tell apart how often from the period a value averages over

- The ground truth triple "weekly (8 day)" (the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0") may become two, or move to the new predicate, depending on the expert's answer to (a).
- One more entity class and predicate in the ground truth schema, for the annotation guidelines and the model to tell apart.

#### Option 3: No temporal resolution for a swath dataset

- The ground truth triple "daily" (the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061") is deleted or moved to another predicate, and the annotation guidelines say when.
- The record states "daily snow cover", so that [fact](../docs/terminology.md#2-triples) must still be written down somehow ("Every fact the record states", rule 2 of "What counts as a fact").

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 10: 3bceffb4-f01e-433c-af79-42b9d9427231
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 15: 32614a2f-a286-4c7c-9f1e-deafdf8bd6a3
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- record at pool position 21: 264a9b23-9a86-46a7-ab61-9661230ea667
- classed triple of the record at pool position 1: "COMET ESCORT 4" (MissionPhase) HAS_TIME_SPAN "2015-10-22 to 2015-12-31" (Time)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_TIME_SPAN "2015-11-01T19:58:35.000 to 2015-11-02T04:59:27.000" (Time)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_GRANULE_DURATION "5 minutes" (Value)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_TEMPORAL_RESOLUTION "daily" (TemporalResolution)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_TEMPORAL_RESOLUTION "weekly" (TemporalResolution)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_TEMPORAL_RESOLUTION "weekly (8 day)" (TemporalResolution)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_TEMPORAL_RESOLUTION "daily" (TemporalResolution)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_TEMPORAL_RESOLUTION "daily" (TemporalResolution)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) HAS_TIME_SPAN "from January, 2007 up to March, 2011" (Time)
- classed triple of the record at pool position 10: "comet escort 1" (MissionPhase) HAS_TIME_SPAN "between 2014-11-19 and 2015-03-10" (Time)
- classed triple of the record at pool position 12: "2XMMi-DR3" (Dataset) HAS_TIME_SPAN "between 2000 February 3 and 2008 October 08" (Time)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_TIME_SPAN "from 2015-08-25T23:25:00.000 to 2015-09-22T23:24:59.000" (Time)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) PRODUCED_USING_ALGORITHM "Average" (Algorithm)
- classed triple of the record at pool position 9: "RDR data" (Dataset) HAS_MISSION_PHASE "encounter" (MissionPhase)
- classed triple of the record at pool position 15: "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data" (Dataset) HAS_TEMPORAL_RESOLUTION "Daily" (TemporalResolution)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) HAS_TEMPORAL_RESOLUTION "daily" (TemporalResolution)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) HAS_TEMPORAL_RESOLUTION "4 s" (TemporalResolution)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_TEMPORAL_RESOLUTION "between 6-12 days" (TemporalResolution)
- classed triple of the record at pool position 19: "2013 balloon campaign" (Campaign) HAS_TIME_SPAN "January and February of 2013" (Time)
- classed triple of the record at pool position 19: "2014 balloon campaign" (Campaign) HAS_TIME_SPAN "January and February of 2014" (Time)
- classed triple of the record at pool position 19: "August 2015 BARREL campaign" (Campaign) HAS_TIME_SPAN "August 2015" (Time)
- classed triple of the record at pool position 19: "2016 campaign" (Campaign) HAS_TIME_SPAN "2016" (Time)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_TIME_SPAN "from 2013 to 2016" (Time)
- classed triple of the record at pool position 21: "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (Dataset) HAS_TIME_SPAN "from November 2008 through August 2009" (Time)
- classed triple of the record at pool position 25: "Copernicus Sentinel data" (Dataset) HAS_TIME_SPAN "2024-2025" (Time)
- translation table row: entity class Frequency
- translation table row: predicate HAS_TIME_RESOLUTION
- translation table row: predicate HAS_DURATION
- translation table row: predicate COVERS
- translation table row: predicate HAS_FREQUENCY
- ground truth schema entry: entity class TemporalResolution
- ground truth schema entry: predicate HAS_TEMPORAL_RESOLUTION
- ground truth schema entry: predicate HAS_GRANULE_DURATION
- ground truth schema entry: predicate HAS_TIME_SPAN
- rule: Writing a classed triple, rule 19
- rule: Writing a classed triple, rule 21
- pipeline method: 040_induce_schema/run.py: how the current schema is learned (the old option 4, in My notes: splitting a broad predicate or entity class)

## Q6: Processing levels: what is L2G, and which list should the ground truth follow?

- status: open
- priority: medium
- question kind: schema entry
- in short: the ground truth schema's ProcessingLevel and HAS_PROCESSING_LEVEL, and a reference list of processing levels

### The question

Records write how far their data have been processed, the processing level, in many ways: "Level-2 (L2)", "Level-3", "Level 3", "L2", "L2G", and perhaps "1/2/3". So far we keep each record's own words, so two records that write one level in two wordings ("Level 3" and "L3") give two different values in the knowledge graph; a reference list would give one. We would like to know:

- (b) Which list of processing levels should we follow? Our plan, for now, is a list that records each value's scheme, since the same words mean different things in different schemes (a Planetary Data System "Level 2" is CODMAC level 2, NASA's Level 0), with every spelling ("Level 3", "L-3") matched to a value of its own scheme. The one we know of is NASA Earthdata's *Data Processing Levels* (Level 0, Level 1A, 1B, 1C, Level 2, 2A, 2B, Level 3, 3A, Level 4; https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/data-processing-levels). Does it hold for the whole catalog, or do other parts of NASA, e.g. the Planetary Data System, use other levels? If there are two lists, how do they line up?

### Example record

- record id: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- pool position: 6
- title: MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid
- notes: The Moderate Resolution Imaging Spectroradiometer (MODIS) Near Real Time (NRT) Combined Terra and Aqua Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product (MCD19A2N) produced daily at 1 kilometer (km) pixel resolutions. The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product.
- source text: L2G
- source text: gridded Level 2 product
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_PROCESSING_LEVEL "Level 2" (ProcessingLevel)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation)

### Ground truth schema

- entity class ProcessingLevel: a stage of processing: how far data have been processed from what the Instrument recorded, e.g. Level 2
- predicate HAS_PROCESSING_LEVEL: is processed to this ProcessingLevel

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or abbreviation stands for.

### Options

#### Option 1: Keep each record's own words

The processing level is the record's words, as written ("Level-2 (L2)", "Level-3", "Level 3", "L2"), and a code the record doesn't explain ("1/2/3") gives no fact.

#### Option 2: A closed list of processing levels

We list the processing levels (from the list your answer to (b) names), and write the value of the list that the record's words mean ("Level-2 (L2)" becomes "Level 2").

#### Option 3: Own words now, the list's value added later

We keep each record's own words, and add the value of the list each wording means to the knowledge graph later, next to the record's words.

### My current reading

Option 1 for now, because it writes only the record's own words. We would move to option 2 or 3 if your answer to (b) gives one list that covers the catalog.

### My notes

Checked against sources on 2026-10-30 (PDS3 Standards Reference, chapter 6, https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf; ESA, ROSETTA Archive Conventions, RO-EST-TN-3372): in the titles, "1/2/3" are CODMAC processing levels 1, 2 and 3; "CAL" is the target CALIBRATION, not "calibrated"; "EDR" and "RDR" are data set types (Experiment and Reduced Data Record), not levels; the pairing "Level 2 (EDR)" and "Level 3 (RDR)" in the Stardust record is the data set's own. The level schemes differ: a PDS "Level 2" (CODMAC) is edited raw data, NASA Earthdata's Level 0, while an Earthdata "Level 2" is derived variables (https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/data-processing-levels); PDS4 uses words instead, with no official crosswalk. MODIS "L2G" is both "Level 2 gridded" and a level label of its own (NASA's catalog gives ProcessingLevel "2G").

Five of the tuning records we have annotated so far write a processing level, or a code that may be one: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0", "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061", "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005", "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" and "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (the last is in the ground truth now); every classed triple the answer may change is listed under Affects. The example is the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid".

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) and (c) are the old (a) and (c); their (b) keeps the old (b)'s question about how the Planetary Data System's names are built. Left for us, to settle from their answer to (b) (and the Planetary Data System's own documents): the pairing of "2/3" with "EDR/RDR" in the record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0", whether "CODMAC level 2" in the record "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" confirms the reading of the title's level, and "INFLDSTR", which the notes of the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" already explain. The options' titles and texts no longer say "ground truth"; their meaning is the same.

- (a) The example below has "L2G" in its title and "gridded Level 2 product" in its notes. Is L2G "Level 2, gridded": a processing level (Level 2) plus a layout on a grid, which the ground truth writes as two [facts](../docs/terminology.md#2-triples)? Or is L2G a processing level of its own?
- (b) The record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0", from the Planetary Data System, has "RSI 1/2/3" in its title. Are 1, 2 and 3 processing levels of the data from the instrument RSI? Our reading, not checked against a source: they may be levels of a planetary data scale, but the record doesn't say so, and the annotation guidelines say never to write down what an unexplained code stands for, so the ground truth has no processing level for this record. If they are levels, are they CODMAC levels (our reading, not checked against a source: the Planetary Data System has numbered its data's processing levels by the CODMAC scale)? And what does "1149" stand for, in the same title's "COMET ESCORT 4 1149 V1.0"? If the Planetary Data System's data set names give it a fixed place with a fixed meaning, should the ground truth write it as a fact of its own? One answer about how these data set names are built would settle both codes. The record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" has "DFMI 2/3" in its title, and its notes say "This data set contains Level 2/3 (EDR/RDR) data". We read "2/3" as two levels, paired in order with "EDR/RDR", and wrote two facts: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) HAS_PROCESSING_LEVEL "Level 2 (EDR)" (ProcessingLevel) and "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) HAS_PROCESSING_LEVEL "Level 3 (RDR)" (ProcessingLevel). Is that pairing right, and does this record confirm the reading of "1/2/3" above? The record "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" has "ALICE 2" in its title, and its notes say "This data set contains CODMAC level 2 data", which we wrote as "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (Dataset) HAS_PROCESSING_LEVEL "CODMAC level 2" (ProcessingLevel). Its title also has "67P/CAL", which the record doesn't explain, so we wrote nothing for "CAL": what does it stand for (our reading, not checked against a source: calibration)? The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" has three more such codes in its title: "MTP020" (after "ESC3", which its notes write as "the COMET ESCORT 3 mission phase"), "RDR" and "INFLDSTR"; for the last, the notes have "in-field stray-light corrected". We wrote nothing for "MTP020" and "RDR". What do they stand for?
- (c) Which list of processing levels should the ground truth follow? The one we know of is NASA Earthdata's *Data Processing Levels* (Level 0, Level 1A, 1B, 1C, Level 2, 2A, 2B, Level 3, 3A, Level 4; https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/data-processing-levels). Does it hold for the whole catalog, or do records of other parts of NASA, e.g. the Planetary Data System, use other levels? If there are two lists, how do they line up?

The question's context, as it was: Of the records we have read so far, the example below is the one whose "L2G" we are least sure of. The record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" has two levels: "Level 3" for its own dataset, and "L2" for the pixels it was made from ("the L2 pixels are binned").

The knowledge graph will be built from the records' metadata fields and the extracted triples. Two records that write one level in two wordings ("Level 3" and "L3") give two different object instances; a reference list would give one.

The options as they were, before 2026-10-26: Option 1, Keep each record's own words: the object instance of HAS_PROCESSING_LEVEL is the record's words, as written ("Level-2 (L2)", "Level-3", "Level 3", "L2"), and a code the record doesn't explain ("1/2/3") gets no ground truth triple. Option 2, A closed list of processing levels in the ground truth: the ground truth schema lists the processing levels (from the list your answer to (c) names), and the object instance is the value of the list that the record's words mean ("Level-2 (L2)" becomes "Level 2"). Option 3, Own words in the ground truth, the list's value added later: the ground truth keeps each record's own words; the value of the list each wording means is added to the knowledge graph in a later stage, next to the record's words.

Taken out of the expert's view on 2026-10-31, as a question we can settle from sources; kept here word for word. The title was "Processing levels: what is L2G, what are "1/2/3" in a Planetary Data System title, and which list should the ground truth follow?". The expert's (b) is now the old (c), and the options and my current reading say "(b)" where they said "(c)". The old (b) is answered by the data sets' own catalog files and by the PDS3 Standards Reference, chapter 6 (https://pds.nasa.gov/datastandards/pds3/standards/sr/Chapter06.pdf), which builds each data set name from up to seven components (instrument host, target, instrument, CODMAC processing level number, data set type, description, version), with "/" read as "and": "1/2/3" are CODMAC levels 1, 2 and 3, "(Data set contains raw, edited and calibrated data)" (the data set's DATASET.CAT, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/); "1149" is a running measurement number, "incremented measurement by measurement" (the same catalog); "CAL" is the target CALIBRATION, not "calibrated" (https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/ALICE/RO-C-CAL-ALICE-2-ESC1-V1.0/CATALOG/DATASET.CAT); "MTP020" is planning period 20 inside the phase COMET ESCORT 3 (the Rosetta NAVCAM archive's table, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/NAVCAM/RO-C-NAVCAM-2-ESC1-MTP010-V1.1/DOCUMENT/RO-SGS-IF-0001.ASC); "RDR" is the data set type Reduced Data Record, not a level. annotations/left_out.md gives each, under its record. None of the records explains these codes, so they still give no ground truth triple (rule 1 of *What counts as a fact*).

- (b) How are the Planetary Data System's data set names built? The record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" has "RSI 1/2/3" and "1149" in its title, and its notes explain neither. Are 1, 2 and 3 processing levels (of the CODMAC scale?), and what is "1149"? Other titles have more such codes: "67P/CAL" (the record "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0"), and "MTP020" and "RDR" (the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0"). We write down only what a record explains, so for now these codes give no facts.

Taken out of the expert's view on 2026-10-31, as settled from sources (the research of 2026-10-31); kept here word for word: "- (a) The example below has "L2G" in its title and "gridded Level 2 product" in its notes. Is L2G "Level 2, gridded": a processing level (Level 2) plus a layout on a grid, two facts? Or is L2G a processing level of its own?" My current reading ended: "For the example, we have written "Level 2" and "gridded" as two facts, our reading of "gridded Level 2 product"; your answer to (a) tells us whether that is right." The (b)'s plan, as it was (it no longer matched the decision of 2026-10-31, research B1, in docs/improvements.md, *Linking subject instances and object instances to reference lists*): "Our plan, for now, is a short list: L0, L1A, L1B, L2, L3, L4, with every spelling ("Level 3", "L-3") matched to one of them."

Checked on 2026-10-31, the old (a): both readings are true. NASA's metadata treats L2G as a level of its own (CMR's ProcessingLevel Id "2G") and defines it as Level 2 data on a grid: "Level 2G data products are derived geophysical variables at the same resolution and location as the Level 1 source data mapped on a uniform space-time grid scale (Sinusoidal)" (MCD19A2's collection record, https://cmr.earthdata.nasa.gov/search/concepts/C2324689816-LPCLOUD.umm_json); the research of 2026-10-30 (G6) found the same in NASA LAADS and the snow product's guide. So the two facts the ground truth writes from "gridded Level 2 product" stand (option 1); a later list of levels must contain "2G".

### Quoted for us

- entity class ProcessingLevel -> ProcessingLevel: A designation of how far a data product has been processed from raw instrument output, such as Level 0 through Level 3 or Near Real Time.
- predicate HAS_PROCESSING_LEVEL -> HAS_PROCESSING_LEVEL: The subject (a data product) has the object as its data processing level, such as L0, Level-2 or Level-3.
- Writing a classed triple, rule 11: Subject instance and object instance: the record's own words, as written.
- Writing a classed triple, rule 19: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 20: A name with its own abbreviation, another name or code of its own, or a short note in parentheses is one instance, as written. Suppose: a record says "This Level-2 (L2) dataset". Then: the instance is "Level-2 (L2)", with no ALSO_KNOWN_AS triple.
- Writing a classed triple, rule 23: One thing, one wording, within a record.

### Consequences

#### Option 1: Keep each record's own words

- No change to the ground truth triples listed under Affects, nor to the annotation guidelines.
- One processing level is written in several ways across records ("Level-2 (L2)", "L2", "Level 2"), so a search of the knowledge graph for Level 2 data has to know every wording.

#### Option 2: A closed list of processing levels

- A new exception to rule 11 of "Writing a classed triple" (quoted above, for us), written in the annotation guidelines and in the copy of the rules the [model](../docs/terminology.md#8-the-pipeline) follows, which both change.
- The ground truth triples listed under Affects are checked again, and some object instances change.
- Every record names a processing level the same way, so a search needs one value; a code such as "1/2/3" still gets a value only if the record explains it.
- A record's level that isn't on the list has no value to use, unless the list covers the whole catalog.

#### Option 3: Own words now, the list's value added later

- The annotation guidelines and the ground truth don't change, and the knowledge graph can still be searched by the list's values.
- Work to match each wording to a value of the list, outside the ground truth, which this project hasn't planned yet.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 10: 3bceffb4-f01e-433c-af79-42b9d9427231
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- record at pool position 21: 264a9b23-9a86-46a7-ab61-9661230ea667
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_PROCESSING_LEVEL "Level-2 (L2)" (ProcessingLevel)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_PROCESSING_LEVEL "Level-3" (ProcessingLevel)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_PROCESSING_LEVEL "Level 3" (ProcessingLevel)
- classed triple of the record at pool position 4: "pixels" (Dataset) HAS_PROCESSING_LEVEL "L2" (ProcessingLevel)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_PROCESSING_LEVEL "Level 2" (ProcessingLevel)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_PROCESSING_LEVEL "L3" (ProcessingLevel)
- classed triple of the record at pool position 9: "EDR (raw) sensor data" (Dataset) HAS_PROCESSING_LEVEL "Level 2" (ProcessingLevel)
- classed triple of the record at pool position 9: "RDR data" (Dataset) HAS_PROCESSING_LEVEL "Level 3" (ProcessingLevel)
- classed triple of the record at pool position 10: "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (Dataset) HAS_PROCESSING_LEVEL "CODMAC level 2" (ProcessingLevel)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_PROCESSING_LEVEL "CODMAC level 4" (ProcessingLevel)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) HAS_PROCESSING_LEVEL "L3" (ProcessingLevel)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) HAS_PROCESSING_LEVEL "Level 2" (ProcessingLevel)
- classed triple of the record at pool position 21: "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (Dataset) HAS_PROCESSING_LEVEL "L0" (ProcessingLevel)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_PROCESSING_LEVEL "Level 3" (ProcessingLevel)
- classed triple of the record at pool position 24: "HIRDLS profiles" (Dataset) HAS_PROCESSING_LEVEL "Level 2" (ProcessingLevel)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_PROCESSING_LEVEL "Level-3" (ProcessingLevel)
- translation table row: entity class ProcessingLevel
- translation table row: predicate HAS_PROCESSING_LEVEL
- translation table row: predicate HAS_PROPERTY
- ground truth schema entry: entity class ProcessingLevel
- ground truth schema entry: predicate HAS_PROCESSING_LEVEL
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 11
- rule: Writing a classed triple, rule 19
- rule: Writing a classed triple, rule 20
- rule: Writing a classed triple, rule 23
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which a list of processing levels to follow would change

## Q7: A processing step: what is its input, and what is its method?

- status: open
- priority: medium
- question kind: rule
- in short: rule 24 of the annotation guidelines (a processing step), and the ground truth schema's COMPUTED_FROM and PRODUCED_USING_ALGORITHM

### The question

When a record describes how its data were made, we write the step as output = method(input): the output is COMPUTED_FROM each input ("was made by processing this input"), and PRODUCED_USING_ALGORITHM the method ("was made or detected by applying this Algorithm"). In some records we are not sure which part is the input, and we would like a general way to tell. We would like to know:

- (a) The example below says its two sea surface temperature (SST) products are "derived from the long wave IR 11 and 12 micron wavelength channels" and generated "using the mid-infrared 3.95 and 4.05 micron wavelength channels". We wrote each channel as an input. Is it right to say that an SST product is computed from a wavelength channel? Our reading, not checked against a source: it is computed from what the instrument measured in those channels, and the channel says where in the spectrum that was. If a channel is not an input, how would you say it: "uses the 11 micron channel", "is measured in the 11 micron channel", or something else?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels
- source text: At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4
- source text: The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm
- classed triple: "skin SST" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple: "skin SST" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)
- classed triple: "skin SST" (Variable) PRODUCED_USING_ALGORITHM "modified nonlinear SST algorithm" (Algorithm)

### Ground truth schema

- predicate COMPUTED_FROM: was made by processing this input
- predicate PRODUCED_USING_ALGORITHM: was made or detected by applying this Algorithm
- entity class Channel: a range of wavelengths an Instrument measures separately, e.g. 11 micron channel
- entity class Algorithm: a method applied to data to compute a result, e.g. series of screens; modified nonlinear SST algorithm

### Options

#### Option 1: Keep the inputs as they are

The channels stay inputs: "skin SST" COMPUTED_FROM "long wave IR 11 micron wavelength channel".

#### Option 2: A predicate of its own for the channels a product uses

A new predicate for "uses the measurements of this Channel", for the channels, in place of COMPUTED_FROM.

### My current reading

Option 1 until you answer, because the record's own words are "derived from", which read to us as an input used in the computation. If your answer to (a) is that a channel is not an input, we would choose option 2, since a fact should say what is true.

### My notes

Of the first seven records of the pool, all tuning records, four describe a processing step: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061", "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" and "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (the last is in the ground truth now); and so do "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006", "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0", "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" and "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (decided 2026-10-25, for us to confirm; settled on 2026-10-31, below, *Checked on 2026-10-31, the old (c)*: no change; (e) is about the last one's). All their classed triples with COMPUTED_FROM or PRODUCED_USING_ALGORITHM are listed under Affects. The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0"; the settled one is the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0".

Pending facts, for the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (ab33f184, in the ground truth now without them; decided 2026-10-25, for us to confirm; settled on 2026-10-31, below, *Checked on 2026-10-31, the old (c)*: they stay left out, and annotations/left_out.md keeps them), each added if the answer to (e) says such corrections should be kept: the four statements "solar stray-light corrected", "in-field stray-light corrected", "radiometric calibrated" and "geometric distortion corrected (resampled)", each with a predicate to decide.

Rule 24 now says: "A word that says only that something was done ("corrected", "calibrated", "detrended") names no method." If the answer to (e) says such words should be kept, they would be a triple of another predicate, not PRODUCED_USING_ALGORITHM.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) now holds the old (a) and (b); their (b) is the old (c); their (c) the old (e) (so "the answer to (e)" above is now their answer to (c)). The old (d), how to write each channel after splitting a list, we settle ourselves (it follows the rule for lists, rule 22, and the expert can say so under (a) if it reads wrong). The example no longer shows two of its passages and their classed triples, not needed for the question, which stay in the ground truth: source text "To generate the L3 products the L2 pixels are binned", with "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) COMPUTED_FROM "pixels" (Dataset) (in Affects); and source text "the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS", with "mid-infrared 3.95 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) and "mid-infrared 4.05 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument).

The question's opening, as it was: Rule 24 of the annotation guidelines (quoted below) writes each processing step a record describes as output = method(input): the output COMPUTED_FROM ("was made by processing this input") each input, and the output PRODUCED_USING_ALGORITHM ("was made or detected by applying this Algorithm") the method. In one record we are not sure which part is the input, and we would like a general way to tell. We would like to know:

- (a) The example below says its two sea surface temperature (SST) products are "derived from the long wave IR 11 and 12 micron wavelength channels" and generated "using the mid-infrared 3.95 and 4.05 micron wavelength channels". We wrote each channel as an input: COMPUTED_FROM, with a Channel ("a range of wavelengths an Instrument measures separately") as its object instance. Is it right to say that an SST product is computed from a wavelength channel? Our reading, not checked against a source: it is computed from what the instrument measured in those channels, and the channel says where in the spectrum that was, not what was processed.
- (b) If a channel is not an input: how would you say it? Is "uses the 11 micron channel" or "is measured in the 11 micron channel" a relationship of its own, apart from "is computed from"?
- (c) Is there a general way to tell an input from a method, that would settle the case above and others like it? For example, the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says its index "is derived from radiance data", which we wrote as an input, and the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" names its product a "Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product", which we write as made using MAIAC, a method.
- (d) We split "the long wave IR 11 and 12 micron wavelength channels" into "long wave IR 11 micron wavelength channel" and "long wave IR 12 micron wavelength channel" (rule 22, quoted below). Would someone in your field write each channel that way?
- (e) The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" says its data set "contains solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data". Each word names a step and what it corrects, though only as a participle. We left each out for now (decided 2026-10-25, for us to confirm); they would be methods: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) PRODUCED_USING_ALGORITHM "solar stray-light corrected" (Algorithm), and the same for "in-field stray-light corrected", "radiometric calibrated" and "geometric distortion corrected (resampled)". Elsewhere, where a record has only a verb ("binned", "detrended", "convert", "cross-correlated"), we wrote no method. Is a participle that names what was corrected or calibrated a method, and should it be written in the record's words ("radiometric calibrated") or as the name of the step ("radiometric calibration")?

The question's context, as it was: The example below has products computed from channels, and facts that say which channels are unique to MODIS.

Settled, so not asked here: the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "The nominal fast neutron count rates were detrended using the GRaND epithermal neutron map to produced this residual map", and we wrote the epithermal neutron map as an input, COMPUTED_FROM, beside the count rates. A review of that record on 2026-10-22 checked NASA's archive documents for it: the epithermal neutron map is used to correct the fast neutron counts, so it is an input. No method is written for that record, since "detrended" names an operation but no algorithm with a name of its own.

Option 2, as it was: Coin a predicate in the ground truth schema for "uses the measurements of this Channel", and write the channels with it instead of COMPUTED_FROM. My current reading, as it was, ended: "Your answer to (c) would become part of rule 24."

Changed on 2026-10-31: the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" now keeps the four words in the instance of what its dataset holds, "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_SPATIAL_REPRESENTATION "solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data" (SpatialRepresentation), in place of "image data in W/m^2/sr/nm", by rule 24's "Words that name no method" ("it stays in the instance, as written") and rule 22's "Describing words joined by "and" or a comma" (they describe one word, "image data", so they stay whole); the expert's (c) says so. The pending facts above stay pending. In the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid", the subject of the step the record states ("used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product") is now "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" (Dataset), the wording the record gives first (rule 23), in place of "MCD19A1N".

Added to the expert's (c) on 2026-10-31, nothing taken out: "; the words stay in the instance of what the dataset holds".

Added on 2026-10-31, listed under Affects: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) PRODUCED_USING_ALGORITHM "Average" (Algorithm) (decided on 2026-10-31: the record's "Average daily, weekly (8 day) … products" names the method, averaging, as the land surface temperature record's "the average of all qualifying observations" would if it were not hedged) and "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) PRODUCED_USING_ALGORITHM "structure function (SF)" (Algorithm) (Q26, settled on 2026-10-31).

Taken out of the expert's view on 2026-10-31, as settled (the research of 2026-10-31, and my decisions of that day); kept here word for word: "- (b) Is there a general way to tell an input from a method? For example, the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says its index "is derived from radiance data", which we wrote as an input, and the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" names its product a "Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product", which we wrote as made using MAIAC, a method." "- (c) Is a word that says what was corrected or calibrated a method? The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" holds "solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data". For now we write no method for such words, nor for a bare verb ("binned", "detrended"); the words stay in the instance of what the dataset holds. If they are methods, should they be written in the record's words ("radiometric calibrated") or as the name of the step ("radiometric calibration")?" My current reading ended: "Your answer to (b) would become part of how we write a processing step."

Decided on 2026-10-31, the old (b): the field's test goes into rule 24 of *Writing a classed triple* (both copies; the model's with an invented example), as its part *Input or method*: "A method is what could be applied again to other data (an algorithm, a procedure, and its settings, such as coefficients tuned per month); an input is the data the step was applied to, which its output is made from." Its sources: W3C SOSA/SSN, a procedure "is re-usable, and might be involved in many Observations", and an input is "Any information that is provided to a Procedure for its use" (https://www.w3.org/TR/vocab-ssn/); W3C PROV-O keeps a plan, "a set of actions or steps intended by one or more agents to achieve some goals", apart from what an activity used (https://www.w3.org/TR/prov-o/). The research of 2026-10-30 (M10) fits it: coefficients tuned per month and latitude band belong to the method. By it, "radiance data" is an input and MAIAC a method, as the ground truth has them; no ground truth triple changes.

Checked on 2026-10-31, the old (c): each of the four words refers to a named, documented calibration step of the OSIRIS pipeline. The data set's *OSIRIS calibration pipeline OsiCalliope* (OSIRIS_CAL_PIPELINE_V08.PDF, which its catalog file cites, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/OSINAC/RO-C-OSINAC-4-ESC3-67P-M20-INFLDSTR-V1.0/DOCUMENT/CALIB/) "executes the required calibration steps sequentially on the data", among them "Correction of solar stray light", "Correction of in-field stray light", "Radiometric calibration" and "Correction of geometric distortion", the last done "by resampling the images" (so "(resampled)" is a short note on the same step, rule 20). Decided on 2026-10-31: no change. The record's participles stay in the instance of what the dataset holds (rule 24's *Words that name no method*), and the steps' names are not the record's words (rule 11), so they go to docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080). The four items of annotations/left_out.md stay, now pointing here.

### Quoted for us

- entity class Variable: a property narrowed by a method, a band, a threshold, another object or another constraint, e.g. SST4; NDSI; band 31 emissivity; dust fluences at each of twelve mass thresholds
- predicate UNIQUE_TO_INSTRUMENT: is found only on this Instrument
- entity class Wavelength -> Channel: A wavelength band or spectral range, such as an infrared filter band, in which observations are made.
- predicate DERIVED_FROM -> COMPUTED_FROM: The subject (a data product, quantity, value or format) is computed from or based on the object, a source measurement, signal, input data or prior standard.
- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or abbreviation stands for.
- Writing a classed triple, rule 22: A list: one ground truth triple per item. Apply rule 19 first. Then put one item alone in the list's place (the subject or the object), with the words the items share copied onto it. Each item is now one thing, so shared words that agree with the number of items are put in the singular to agree with one item ("channels" → "channel"; "are" → "is"); each item's own words stay as written ("oceans"). An item that names no specific thing ("his team") gives no ground truth triple (rule 9 of What counts as a fact: "Not a fact without a specific thing"). Suppose: a record says the SST is "derived from the long wave IR 11 and 12 micron wavelength channels". Then: two ground truth triples, with the objects "long wave IR 11 micron wavelength channel" and "long wave IR 12 micron wavelength channel".
- Writing a classed triple, rule 24: A processing step: output = method(input). For each processing step the record describes, find what it made (the output), what it was made from (the input), and how (the method). Each step gives up to two ground truth triples, each written only if the record names both of its ends

### Consequences

#### Option 1: Keep the inputs as they are

- No change to the ground truth triples listed under Affects.
- If the expert's answer to (a) is that a channel is not an input, the ground truth says the product was made by processing a range of wavelengths, which is not literally true.

#### Option 2: A predicate of its own for the channels a product uses

- The four ground truth triples with COMPUTED_FROM and a Channel, below, change to the new predicate.
- COMPUTED_FROM keeps one meaning, an input that was processed; one more predicate for the annotation guidelines and the [model](../docs/terminology.md#8-the-pipeline) to use.
- The schema the model extracts with has DERIVED_FROM (translated to COMPUTED_FROM, in the translation table, quoted above for us); an extracted triple of DERIVED_FROM with a channel would then no longer agree with the ground truth unless the translation depends on the object instance's entity class.

### Affects

- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) COMPUTED_FROM "Normalized Difference Snow Index (NDSI)" (Variable)
- classed triple of the record at pool position 2: "Normalized Difference Snow Index (NDSI)" (Variable) COMPUTED_FROM "radiance data" (Dataset)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) PRODUCED_USING_ALGORITHM "series of screens" (Algorithm)
- classed triple of the record at pool position 4: "skin SST" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "skin SST" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) COMPUTED_FROM "pixels" (Dataset)
- classed triple of the record at pool position 4: "skin SST" (Variable) PRODUCED_USING_ALGORITHM "modified nonlinear SST algorithm" (Algorithm)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) COMPUTED_FROM "nominal fast neutron count rates" (Variable)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) COMPUTED_FROM "GRaND epithermal neutron map" (Dataset)
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 15: 32614a2f-a286-4c7c-9f1e-deafdf8bd6a3
- record at pool position 16: ec41fd5d-1159-4aa8-9803-5346e2324a20
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) PRODUCED_USING_ALGORITHM "Multi-Angle Implementation of Atmospheric Correction (MAIAC)" (Algorithm)
- classed triple of the record at pool position 6: "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) COMPUTED_FROM "MOD11_L2" (Dataset)
- classed triple of the record at pool position 7: "band 31 emissivity" (Variable) COMPUTED_FROM "land cover types" (PhysicalQuantity)
- classed triple of the record at pool position 7: "band 32 emissivity" (Variable) COMPUTED_FROM "land cover types" (PhysicalQuantity)
- classed triple of the record at pool position 9: "RDR data" (Dataset) COMPUTED_FROM "EDR (raw) sensor data" (Dataset)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) COMPUTED_FROM "2XMMi-DR3" (Dataset)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) COMPUTED_FROM "DR7 edition of the SDSS Quasar Catalog" (Dataset)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) COMPUTED_FROM "table1.dat" (Dataset)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_SPATIAL_REPRESENTATION "solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data" (SpatialRepresentation)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) PRODUCED_USING_ALGORITHM "Average" (Algorithm)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) PRODUCED_USING_ALGORITHM "structure function (SF)" (Algorithm)
- classed triple of the record at pool position 15: "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data" (Dataset) COMPUTED_FROM "original trajectory data" (Dataset)
- classed triple of the record at pool position 16: "calibrated values" (Dataset) COMPUTED_FROM "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (Dataset)
- classed triple of the record at pool position 18: "BRDF/Albedo values for VIIRS band M4" (Variable) COMPUTED_FROM "BRDF geometric parameter for VIIRS band M4 (0.555 μm)" (Variable)
- classed triple of the record at pool position 24: "Geopotential Height Zonal Fourier Coefficients" (Variable) COMPUTED_FROM "HIRDLS profiles" (Dataset)
- classed triple of the record at pool position 24: "precision values" (Variable) COMPUTED_FROM "differences between the estimated fields and the input data" (Variable)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) COMPUTED_FROM "Sentinel-1 radar observations" (Dataset)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) COMPUTED_FROM "Copernicus Sentinel data" (Dataset)
- classed triple of the record at pool position 15: "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data" (Dataset) PRODUCED_USING_ALGORITHM "Mean of Date" (Algorithm)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) PRODUCED_USING_ALGORITHM "accumulations" (Algorithm)
- classed triple of the record at pool position 24: "Geopotential Height Zonal Fourier Coefficients" (Variable) PRODUCED_USING_ALGORITHM "Kalman filter using both forward and backward passes in time" (Algorithm)
- classed triple of the record at pool position 24: "precision values" (Variable) PRODUCED_USING_ALGORITHM "root-mean square" (Algorithm)
- translation table row: predicate DERIVED_FROM
- translation table row: predicate USES
- ground truth schema entry: predicate COMPUTED_FROM
- ground truth schema entry: predicate PRODUCED_USING_ALGORITHM
- rule: Writing a classed triple, rule 22
- rule: Writing a classed triple, rule 24
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of rule 24, which a general way to tell an input from a method would change

## Q8: Organizations, teams, roles, programs, facilities and places: which entity class?

- status: open
- priority: medium
- question kind: schema entry
- in short: the ground truth schema's Organization, Role and BASED_IN, and the translation table's rows for Program, Facility, Location and LOCATED_IN

### The question

The records name groups of people, offices, programs and sites, and some name places. Our schema has an entity class for a group with a name of its own, Organization (defined below), and none for a place other than a country. We would like to know:

- (c) Facilities and places: in this catalog, is a facility (a space center, an observatory, a ground station) an organization, a place, or either one, depending on the sentence? And do the records name places (a research station, a field of the sky, a site) often enough, in facts that matter, for us to add an entity class for places?

### Ground truth schema

- entity class Organization: a named institution or one of its named parts, not a Mission, e.g. NASA; OBPG

### Options

#### Option 1: Keep the line as it is

A named group or office is an Organization; a group without a name of its own gives no fact; what an Organization is there for (the official archive for SST) is a Role it holds. A facility counts as an Organization; places other than countries get no entity class.

#### Option 2: Places get an entity class of the ground truth schema

When a record names a place in a fact of its own, our schema gets an entity class for places (and a predicate, "is located in this place"); a facility is a place or an Organization, as your answer to (c) says.

### My current reading

Option 1, for now: so far no fact we wrote depends on a facility or a place other than a country. We would choose option 2 once a record states a fact about a place.

### My notes

The record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" adds "NASA HEASARC" (Organization), written so by rule 23, though the record also writes "the HEASARC" (decided 2026-10-25, for us to confirm); its "the authors" are left out for now, with the study they belong to (Q26). The ground truth schema's entity class Team ("a group of people without a name of its own, e.g. Peter Minnett and his team") was removed on 2026-10-30: a named group is an Organization, and an unnamed group names no specific thing, so it gives no fact (What counts as a fact, rule 9, as with "his team" that day); the expert's question, (a) and option 1 were reworded then. The groups appear as the subject instance or object instance of the classed triples listed under Affects; the example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", and the program of the old (c) (now the expert's (b)) is the record "NASA Standards and and Technical Assistance Resource Tool"'s. The facts about a country are the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005"'s: rule 19 of *Writing a classed triple* makes a country that qualifies an organization ("U.S. National Aeronautics and Space Administration (NASA)") a ground truth triple of its own.

The model extracts classed triples with the current schema. Before they are compared with the ground truth, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names; a row that names (none): a classed triple that uses it always counts as extracted only. We would choose option 4 with the answers to the old (d) to (f) (now the expert's (c)) telling us what to coin, once a tuning record states a fact about a place.

Changed on 2026-10-31: the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" says "Argentina's space agency, Comisión Nacional de Actividades Espaciales (CONAE)". The ground truth no longer has "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization) BASED_IN "Argentina" (Country); it has "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization) SERVES_AS "Argentina's space agency" (Role): a role only CONAE holds (rule 4 of *What counts as a fact*: "A sentence that names one specific role or thing is not an "is a" fact"), and "Argentina's" stays in the instance by rule 19 of *Writing a classed triple*, since taking it out would give a triple that isn't true ("space agency" alone is a type). The ground truth schema's Role now reads "a position only one Person or Organization holds (rule 4), e.g. official archive for SST; Argentina's space agency", and Country "a nation, as where a Person or Organization is based, e.g. U.S.; Argentina". So the only fact about a country is now "National Aeronautics and Space Administration (NASA)" (Organization) BASED_IN "U.S." (Country). The record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" also has, since 2026-10-31, "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) PROVIDED_BY_PARTY "NASA HEASARC" (Organization) ("is provided to users, as a service or as data, by this Person or Organization").

Taken out of the expert's view on 2026-10-31, kept here word for word: the question's opening defined "Role (a position someone holds)"; it now follows the ground truth schema's new definition.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) now holds the old (a) and (b); their (b) the old (c), without its part on "NASA" in the name, which we settle ourselves once (b) is answered; their (c) the old (d) and (e). The old (f) we settle ourselves once a record states a fact about a place that isn't a country (option 4). The first example no longer shows the source texts "JPL acquires MODIS ocean L3 SST data from the OBPG" and "Aqua was launched by NASA", nor the classed triples "JPL" (Organization) OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)" (Organization), "Aqua" (Spacecraft) LAUNCHED_BY_PARTY "NASA" (Organization), and the three "Peter Minnett and his team" (Team) RESPONSIBLE_FOR classed triples ("sea surface temperature algorithm development", "error statistics", "quality flagging") (Task); all are under Affects.

- (a) The example below says that JPL "is the official Physical Oceanography Data Archive (PO.DAAC) for SST". We wrote this down as a role JPL holds. Would you say PO.DAAC is a role (a job JPL does), or an organization of its own (with JPL as where it is, or who runs it)?
- (b) The example also names the "NASA Ocean Biology Processing Group (OBPG)" and "Peter Minnett and his team". We wrote the first as an Organization, since it has a name of its own, and the second as a Team, since it doesn't. Is that line (a name of its own, or not) the right one?
- (c) The record "NASA Standards and and Technical Assistance Resource Tool" names the "NASA Technical Standards Program", which provides access to standards and sponsors a web tool. We wrote it as an Organization. Is a NASA "program" like this one an organization (an office with staff), or something else, such as a funded effort? And is "NASA" part of the program's name, so that we keep "NASA Technical Standards Program" whole, as we do now, or does it say whose program it is, which would be a fact of its own (the program a part of NASA)?
- (d) In this catalog, is a facility (e.g. a space center, an observatory, a ground station) best thought of as an Organization, as a place, or as both, depending on the sentence?
- (e) Do the records of this catalog name places (a research station, a field of the sky, a site) often enough, and in [facts](../docs/terminology.md#2-triples) that matter enough, that the ground truth schema should have an entity class for them?
- (f) Is "is located in" the same relationship as "is based in this Country" when the place is a country (e.g. a center located in the U.S.)? When the place is not a country (a state, a city, a region), what should it be?

The question's context, as it was: The example below names an archive, a named group and a team. Which entity class each gets decides which predicates fit it (for example, SPONSORED_BY_PARTY joins only an Organization, a Person or a Team), and how a search of the knowledge graph finds it. The only facts about where something is that we have written so far are two of the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005", both about which country an organization belongs to: "National Aeronautics and Space Administration (NASA)" (Organization) BASED_IN "U.S." (Country), and "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization) BASED_IN "Argentina" (Country).

The [model](../docs/terminology.md#8-the-pipeline) that reads the records has its own entity classes, and the translation table (quoted below) says which entity class of the ground truth schema each one means. It has an entity class Program (which means nothing in the ground truth schema: (none)), Facility (which means Organization), Location ((none)), and a predicate LOCATED_IN (which means BASED_IN).

The options as they were worded before 2026-10-26: option 1 also said "The translation table stays as it is: Program and Location mean nothing in the ground truth schema, Facility means Organization, LOCATED_IN means BASED_IN"; option 2 said the role JPL holds "is then written as a fact joining JPL and PO.DAAC, with a predicate the ground truth schema doesn't have yet"; option 4 said "the model's Location and LOCATED_IN mean them; Facility means the place or Organization, as your answer to (d) says".

Taken out of the expert's view on 2026-10-31, as decided by me (the research of 2026-10-31); kept here word for word. The question's opening was: "The records name groups of people, offices, programs, sites and places, and we are not sure we sort them the way someone in the field would. Our schema has two entity classes for groups: Organization (a group with a name of its own, such as NASA) and Role (a position only one person or organization holds); both are defined below. A group without a name of its own (such as "his team") gives no fact, since a fact needs something the record names. It has no entity class for a place. We would like to know:" The sub-questions: "- (a) Is that line right: a group with a name of its own is an Organization, one without gives no fact, and what an organization is there for is a Role it holds? In the first example, we wrote "NASA Ocean Biology Processing Group (OBPG)" as an Organization, "Peter Minnett" as a Person (the record says "Peter Minnett and his team"; "his team" names no team, so it is left out), and "JPL ... is the official Physical Oceanography Data Archive (PO.DAAC) for SST" as a Role that JPL holds. Would you rather call PO.DAAC an organization of its own, run by JPL?" "- (b) The second example says "The NASA Technical Standards Program provides access to NASA developed standards and handbooks". We wrote the program as an Organization, with its name whole, "NASA" included. Is a NASA program like this one an organization (an office with staff), or something else, such as a funded effort?" The two examples were the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (03a09af3-081e-4db6-9e3b-ea7c0e3138bd), source texts "JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST"; "The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)"; "Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging", classed triples "JPL" (Organization) SERVES_AS "official Physical Oceanography Data Archive (PO.DAAC) for SST" (Role); "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" (Organization); "Peter Minnett" (Person) AFFILIATED_WITH "Rosenstiel School of Marine and Atmospheric Science (RSMAS)" (Organization) and the record "NASA Standards and and Technical Assistance Resource Tool" (3122be4c-b9d0-4cc9-b6d3-9b96c6e743da), source texts "The NASA Technical Standards Program provides access to NASA developed standards and handbooks", classed triples "NASA Technical Standards Program" (Organization) PROVIDES_ACCESS_TO_DOCUMENT "NASA developed standards" (Document). The Ground truth schema part also showed Role and SERVES_AS, now under Quoted for us. Option 2, "A named archive or program is an Organization too": "PO.DAAC becomes an Organization of its own, and the NASA Technical Standards Program stays one; JPL's link to PO.DAAC is then a fact of its own, with a new predicate." Option 3, "A program is its own entity class": "A new entity class for a named program, such as the NASA Technical Standards Program, and Organization kept for institutions and their parts." Their consequences, as they were: "Option 2: A named archive or program is an Organization too - A new predicate is coined (for example, for "is run by" or "hosts"), and the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" gets one more classed triple. - Only what the record states may be written (rule 1 of *What counts as a fact*): the record says JPL "is" the archive, not that JPL runs or hosts it, so the new predicate has to say exactly that. - A search of the knowledge graph for PO.DAAC finds it as an organization, like any other data center. Option 3: A program is its own entity class - The translation table's row for the current schema's Program changes from (none) to the new entity class, so the model's Program instances can be compared with the ground truth. - SPONSORED_BY_PARTY and DEVELOPED_BY_PARTY join only an Organization or a Person: they would need the new entity class added, or the record "NASA Standards and and Technical Assistance Resource Tool" changes." Option 4 is now option 2, the same words. My current reading, as it was: "Option 1, for now: it follows the records' own words (JPL "is" the archive), every case above fits it, and so far no fact we wrote depends on a facility or a place other than a country. We would change it if you tell us that PO.DAAC, or a NASA program, is usually thought of as an organization in its own right (option 2 or 3), and choose option 4 once a record states a fact about a place."

Decided on 2026-10-31, the old (a): the line stays (option 1), and JPL keeps the Role: the record's words make the archive something JPL is ("JPL … is the official Physical Oceanography Data Archive (PO.DAAC) for SST"), and our Role matches W3C DCAT's dcat:Role, "the function of a resource or agent with respect to another resource, in the context of resource attribution or resource relationships" (https://www.w3.org/TR/vocab-dcat-3/). Outside the record, NASA's GCMD Providers keywords list PO.DAAC as a provider of its own under JPL, "NASA/JPL/PODAAC", "Physical Oceanography Distributed Active Archive Center, Jet Propulsion Laboratory, NASA" (version 25.1, https://gcmd.earthdata.nasa.gov/KeywordViewer/), and W3C ORG has an org:OrganizationalUnit, "An Organization such as a department or support unit which is part of some larger Organization" (https://www.w3.org/TR/vocab-org/): that fact goes to docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080), not to the ground truth (rule 1 of *What counts as a fact*). "his team" stays left out (rule 9: it names no team); the ACE guidelines would tag such a group of people ("Sets of people who are not formally organized into a unit are to be treated as a Person entity [entity class Person] rather than an Organization entity [entity class Organization]", the LDC's ACE 2005 annotation guidelines, version 6.6, 2008), but they annotate each wording in a text, while a knowledge graph needs a thing it can name.

Decided on 2026-10-31, the old (b): the NASA Technical Standards Program stays an Organization, its name whole (option 1). The field splits: schema.org makes a Project a kind of Organization, "An enterprise (potentially individual but typically collaborative), planned to achieve a particular aim" (https://schema.org/Project), and W3C ORG an org:OrganizationalCollaboration, "A collaboration between two or more Organizations such as a project"; the slot guidelines of the TAC KBP evaluations, which TACRED follows, say "Programs or projects should not be considered organizations" (*TAC KBP 2014 Slot Descriptions*, https://tac.nist.gov/2014/KBP/ColdStart/guidelines/TAC_KBP_2014_Slot_Descriptions_V1.4.pdf); NASA's page says "The NASA Technical Standards Program is sponsored by the NASA Chief Engineer" (https://standards.nasa.gov/program-overview). Option 1 follows the knowledge graph vocabularies; if Q25's hierarchy is built, a program entity class under Organization would fit both sides (my reading).

Checked on 2026-10-31, for the expert's (c): the ACE guidelines tag a facility by the sentence: one organization is "tagged as type Organization when the textual reference is directly referring to the organization and as type Facility when the mention [wording] refers to the physical building" (ACE 2005, section 7, *Cross-Type Metonymy*), which is the expert's third choice; NASA's GCMD files ground stations as platforms ("Permanent Land Sites", "Field Sites", under Land-based Platforms). No annotated record needs a place yet, so the count over the induction candidates still decides option 2.

Checked on 2026-10-31, the old (a), in NASA's metadata: CMR lists "NASA/JPL/PODAAC" as the ARCHIVER data center of the product MODIS_AQUA_L3_SST_MID-IR_8DAY_4KM_NIGHTTIME_V2019.0, beside "OBPG" as its PROCESSOR (C2036881966-POCLOUD), and GCMD's provider names nest it the same way ("NASA/JPL/PODAAC"; also "NASA/GSFC/SED/ESD/GCDC/OB.DAAC"). W3C ORG's org:subOrganizationOf is the field's predicate for such a part. That PO.DAAC "is operated by JPL" comes only from search extracts (strong secondary). The decision above stands: the record's words make the archive something JPL is, and the outside fact goes to docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080).

### Quoted for us

- entity class Role: a position only one Person or Organization holds (rule 4), e.g. official archive for SST; Argentina's space agency
- predicate SERVES_AS: holds this Role
- entity class Country: a nation, as where a Person or Organization is based, e.g. U.S.; Argentina
- predicate AFFILIATED_WITH: works at or belongs to this Organization
- predicate SPONSORED_BY_PARTY: is sponsored by this Person or Organization
- predicate BASED_IN: is based in this Country
- entity class Organization -> Organization: An institution, agency, center, or collaborative body, such as NASA, HEASARC, or CIESIN, responsible for producing, managing, or distributing data or research.
- entity class Team -> Organization: A group of people, such as investigators, specialists or institutional groups, working together on a mission, project or study.
- entity class Program -> (none): A named organized scientific initiative, often a telescope legacy or key program, encompassing coordinated observations and data products.
- entity class Facility -> Organization: A physical site, base, space center or installation, or the organization operating it, where research, launches or observations are carried out.
- entity class Location -> (none): A named geographic, terrestrial, or celestial place or region, such as a research station, sky field, or facility, where observations or activities occur.
- predicate LOCATED_IN -> BASED_IN: The subject (a facility, site, observation or item) is situated at or in the object, a geographic place, region or physical setting.
- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or abbreviation stands for.
- What counts as a fact, rule 4: Not "is a" facts. "MODIS is a spectroradiometer" says what type of thing MODIS is: that belongs in its entity class, not in a classed triple of its own. A sentence that names one specific role is not an "is a" fact, though: Suppose: a record says "JPL is the official Physical Oceanography Data Archive (PO.DAAC) for SST". Then: a ground truth triple, because it names a role only JPL holds, not a type.
- Writing a classed triple, rule 14: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 19: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.

### Consequences

#### Option 1: Keep the line as it is

- Nothing changes in the ground truth triples listed under Affects, the annotation guidelines, or the translation table.
- PO.DAAC appears only inside the Role "official Physical Oceanography Data Archive (PO.DAAC) for SST", so a search of the knowledge graph for PO.DAAC as an organization doesn't find it.
- A facility the model extracts is compared as an Organization: right for a center named as the body that runs something, wrong for a site named as the place where something happens; a classed triple with LOCATED_IN is right when its object instance is a country, and counted wrong when it is any other place.

#### Option 2: Places get an entity class of the ground truth schema

- Places are compared rightly.
- The ground truth schema gains an entity class and a predicate, and the rows of the translation table that point to them are checked again; the model's Location and LOCATED_IN translate to them, and Facility to the place or Organization, as the expert's answer to (c) says.
- It waits for a tuning record that names a place: the annotation guidelines coin an entity class only when a record needs it.

### Affects

- record at pool position 0: 3122be4c-b9d0-4cc9-b6d3-9b96c6e743da
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 0: "NASA Technical Standards Program" (Organization) PROVIDES_ACCESS_TO_DOCUMENT "NASA developed standards" (Document)
- classed triple of the record at pool position 0: "NASA Technical Standards Program" (Organization) PROVIDES_ACCESS_TO_DOCUMENT "NASA developed handbooks" (Document)
- classed triple of the record at pool position 0: "NASA Standards and and Technical Assistance Resource Tool" (WebTool) SPONSORED_BY_PARTY "NASA Technical Standards Program" (Organization)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization)
- classed triple of the record at pool position 3: "National Aeronautics and Space Administration (NASA)" (Organization) BASED_IN "U.S." (Country)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization)
- classed triple of the record at pool position 3: "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization) SERVES_AS "Argentina's space agency" (Role)
- classed triple of the record at pool position 4: "Aqua" (Platform) LAUNCHED_BY_PARTY "NASA" (Organization)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple of the record at pool position 4: "Peter Minnett" (Person) AFFILIATED_WITH "Rosenstiel School of Marine and Atmospheric Science (RSMAS)" (Organization)
- classed triple of the record at pool position 4: "JPL" (Organization) OBTAINS_DATA_FROM "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple of the record at pool position 4: "JPL" (Organization) SERVES_AS "official Physical Oceanography Data Archive (PO.DAAC) for SST" (Role)
- classed triple of the record at pool position 4: "Peter Minnett" (Person) RESPONSIBLE_FOR "sea surface temperature algorithm development" (Task)
- classed triple of the record at pool position 4: "Peter Minnett" (Person) RESPONSIBLE_FOR "error statistics" (Task)
- classed triple of the record at pool position 4: "Peter Minnett" (Person) RESPONSIBLE_FOR "quality flagging" (Task)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) DEVELOPED_BY_PARTY "NASA HEASARC" (Organization)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) PROVIDED_BY_PARTY "NASA HEASARC" (Organization)
- classed triple of the record at pool position 19: "BARREL" (Mission) PART_OF "NASA Living with a Star" (Organization)
- classed triple of the record at pool position 19: "Robyn Millan" (Person) AFFILIATED_WITH "BARREL team" (Organization)
- classed triple of the record at pool position 19: "South African National Antarctic Expedition" (Organization) ALSO_KNOWN_AS "SANAE" (Organization)
- classed triple of the record at pool position 19: "South African National Antarctic Expedition" (Organization) BASED_IN "South African" (Country)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) DEVELOPED_BY_PARTY "OPERA" (Organization)
- classed triple of the record at pool position 25: "OPERA" (Organization) INFORMED_BY "Satellite Needs Working Group (SNWG)" (Organization)
- classed triple of the record at pool position 25: "Satellite Needs Working Group (SNWG)" (Organization) PART_OF "U.S. Government" (Organization)
- classed triple of the record at pool position 25: "Satellite Needs Working Group (SNWG)" (Organization) HAS_PURPOSE "identifying observation needs across U.S. civilian federal agencies" (Purpose)
- classed triple of the record at pool position 25: "Satellite Needs Working Group (SNWG)" (Organization) HAS_PURPOSE "addressing observation needs across U.S. civilian federal agencies" (Purpose)
- classed triple of the record at pool position 25: "Satellite Needs Working Group (SNWG)" (Organization) HAS_TARGET "Earth" (CelestialBody)
- classed triple of the record at pool position 19: "Robyn Millan" (Person) SERVES_AS "BARREL PI" (Role)
- translation table row: entity class Program
- translation table row: entity class Location
- translation table row: entity class Organization
- translation table row: entity class Facility
- translation table row: entity class Team
- translation table row: predicate LOCATED_IN
- ground truth schema entry: entity class Organization

- ground truth schema entry: entity class Role
- ground truth schema entry: predicate SERVES_AS
- ground truth schema entry: predicate BASED_IN
- rule: What counts as a fact, rule 4
- rule: Writing a classed triple, rule 14
- rule: Writing a classed triple, rule 19

## Q9: Whose purpose is it, and is "used to study" a purpose?

- status: withdrawn
- priority: medium
- question kind: schema entry
- in short: the ground truth schema's Purpose and HAS_PURPOSE

### The question

Our schema has an entity class Purpose and a predicate HAS_PURPOSE (both defined below), for what something is meant to achieve. In the example, we wrote the purposes of two things: Aqua's, from "Aqua was launched ... to study the global dynamics of the Earth atmosphere, land and oceans", and an algorithm's, from "a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors". We are not sure how far a purpose should reach:

- (a) Is "to study the global dynamics of the Earth atmosphere, land and oceans" the purpose of Aqua, the spacecraft, as we wrote it (as three purposes, one each for the atmosphere, the land and the oceans, and "Earth" as what Aqua is about), since the sentence is about Aqua? Or would you say it belongs to Aqua's mission, since a satellite mission usually has the science goals? (The record names no mission for Aqua, so we can't write the mission without adding what the record doesn't state.)
- (b) Is what something is used to study a purpose, in your field, or a different relationship, better kept apart? For example "used to study ocean salinity", or a mission's "objective". And is what a method "allows for" its purpose? For example, the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" says its method, the structure function, "allows for an ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived".

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans
- source text: using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors
- classed triple: "Aqua" (Platform) HAS_TARGET "Earth" (CelestialBody)
- classed triple: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the atmosphere" (Purpose)
- classed triple: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the land" (Purpose)
- classed triple: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the oceans" (Purpose)
- classed triple: "modified nonlinear SST algorithm" (Algorithm) HAS_PURPOSE "provide continuity of SST derived from heritage and current NASA sensors" (Purpose)

### Ground truth schema

- entity class Purpose: an aim something is meant to achieve
- predicate HAS_PURPOSE: is meant to achieve

### Options

#### Option 1: Keep it as it is

The purposes stay with what the sentence is about (Aqua), and what something is used to study, or its objective, counts as a purpose.

#### Option 2: What something studies apart from its purpose

A predicate of its own for what a mission, spacecraft or instrument studies (a quantity or a phenomenon), and HAS_PURPOSE kept for aims written as an action ("make it simpler to access…").

### My current reading

Option 1, for now: it writes what each sentence says, about what it is about. We would choose option 2 if you tell us that what a mission studies and what it is meant to achieve are kept apart in your field.

### My notes

All the HAS_PURPOSE classed triples of the records annotated so far are listed under Affects (the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3"'s two, of the old (d), now part of the expert's (b), are pending facts, left out for now: added if the answer to Q26 says yes; decided 2026-10-25, for us to confirm; settled on 2026-10-31, when Q26 was: the aim is a ground truth triple, and what the structure function "allows for" is a final left-out, below; the expert's (b) itself was settled the same day, "(b), decided by me: a use is not a purpose", in My notes below): a web tool's purpose (the record "NASA Standards and and Technical Assistance Resource Tool"), the purposes of a series of screens applied to data (the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061"), and those of Aqua and of an algorithm (the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", the example). The predicates of the old (c) are the current schema's USED_TO_STUDY and HAS_OBJECTIVE.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) is the old (a); their (b) holds the old (c) and (d). The old (b) we settle ourselves: rule 22's own example keeps the phrase whole, and option 2 stays one of the expert's choices.

- (a) The example below says Aqua was launched "to study the global dynamics of the Earth atmosphere, land and oceans". We wrote this as the purpose of Aqua, the spacecraft, because that is what the sentence is about. Would you say it is the spacecraft's purpose, or its mission's (a satellite mission usually has the science goals)? The record names no mission for Aqua, so we can't write the mission without adding what the record doesn't state.
- (b) In that phrase, "Earth" is the body studied. The annotation guidelines take a target body out of an instance as a [fact](../docs/terminology.md#2-triples) of its own (rule 19 of *Writing a classed triple*). We kept the phrase whole, since "study the global dynamics of the atmosphere, land and oceans" without "Earth" no longer says whose atmosphere. Is keeping it whole right, or should "Earth" also be its own fact (Aqua is about the Earth)?
- (c) The [model](../docs/terminology.md#8-the-pipeline) that reads the records has predicates for what something is "used to study" and for its "objective", and the translation table translates both to HAS_PURPOSE. Is "used to study ocean salinity" a purpose, in your field, or a different relationship (what a mission or instrument studies), better kept apart?
- (d) The record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" says "In their study, the authors aimed to determine the ensemble variability properties of two serendipitously selected AGN samples", and that the structure function the authors used "allows for an ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived". We left both out of the ground truth for now (whether a study's aim and method are facts at all, we ask in Q26); they would be purposes: "the authors" (Team) HAS_PURPOSE "determine the ensemble variability properties of two serendipitously selected AGN samples" (Purpose), and "structure function (SF)" (Algorithm) HAS_PURPOSE "ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived" (Purpose). Is what a method "allows for" its purpose? (Whose aim the study's is, the authors' or the table's, we ask with the study's findings, in Q26.)

The question's context, as it was: The purposes we have written so far are a web tool's (the record "NASA Standards and and Technical Assistance Resource Tool"), those of a series of screens applied to data (the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061"), and those of Aqua and of an algorithm (the example below, whose purpose of Aqua the questions above are about).

Changed on 2026-10-30, when rule 22 changed to split every list, after rule 19: rule 19 takes "Earth" out of the purpose (Aqua HAS_TARGET "Earth"), and rule 22 splits the rest into three purposes, so the old option 2 is no longer a choice and was taken out of the expert's view; the old option 3 is now option 2. Kept here as they were: option 1, "The purpose stays with what the sentence is about (Aqua), the phrase stays whole, and what something is used to study, or its objective, counts as a purpose."; option 2, ""Earth" also becomes a fact of its own (Aqua is about the Earth), and the purpose keeps its words.", with its consequences "HAS_TARGET so far joins a Dataset to a CelestialBody; it would join a Spacecraft too, a new pattern." and "The purpose's object instance keeps "Earth" (taking it out would leave "the atmosphere, land and oceans" of no body), so the body is written twice, once inside the purpose."; the Aqua classed triple, "Aqua" (Spacecraft) HAS_PURPOSE "study the global dynamics of the Earth atmosphere, land and oceans" (Purpose).

The options as they were worded before 2026-10-26: option 1, "The purpose stays with what the sentence is about (Aqua), the phrase stays whole with "Earth" in it, and "used to study" and "objective" both count as a purpose."; option 2, ""Earth" becomes a fact of its own, "Aqua" (Spacecraft) HAS_TARGET "Earth" (CelestialBody), and the purpose keeps its words."; option 3, "A predicate of its own for what a mission, spacecraft or instrument studies (a PhysicalQuantity or a Phenomenon), and keep HAS_PURPOSE for aims written as an action ("make it simpler to access…")."

Changed on 2026-10-31, by rule 22's new "Describing words joined by "and" or a comma" ("quickly" and "conveniently" describe one action, "access"): the record "NASA Standards and and Technical Assistance Resource Tool" now has one purpose, "NASA Standards and and Technical Assistance Resource Tool" (WebTool) HAS_PURPOSE "make it simpler for technical people to access NASA technical information quickly and conveniently" (Purpose), in place of two, "NASA Standards and and Technical Assistance Resource Tool" (WebTool) HAS_PURPOSE "make it simpler for technical people to access NASA technical information quickly" (Purpose) and "NASA Standards and and Technical Assistance Resource Tool" (WebTool) HAS_PURPOSE "make it simpler for technical people to access NASA technical information conveniently" (Purpose).

Changed on 2026-10-31, when Q26 was settled: the study's aim is now a ground truth triple of the record's dataset, "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_PURPOSE "determine the ensemble variability properties of two serendipitously selected samples" (Purpose) (rule 19 takes "AGN" out, a target body, already the ground truth triple HAS_TARGET "active galactic nuclei (AGN)"), and the structure function is one too (PRODUCED_USING_ALGORITHM). What the structure function "allows for" still waits on this question's (b): its would-be ground truth triple, "structure function (SF)" (Algorithm) HAS_PURPOSE "ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived" (Purpose), is in annotations/pending_triples.csv, so that step 070 does not count an extracted triple that matches it as wrong.

Withdrawn on 2026-10-31: settled, so it is no longer asked of the experts; kept whole, so that comments filed under its number still find it. (a), from the field's practice: goals are stated on the one item that is both the spacecraft and its mission. Wikidata's P3712, "has goal" ("desired result or outcome"), is used on spacecraft items (Parker Solar Probe "has goal" "solar research"), and NASA's page for Aqua, filed under its missions, gives "Objective: Study Earth's water cycle" (https://science.nasa.gov/mission/aqua/). So the three purposes stay on "Aqua" (Spacecraft), as the record's sentence has them.

(b), decided by me: a use is not a purpose. Wikidata keeps "has goal" (P3712; among its other names, "objective") apart from "has use" (P366, "main use of the subject (includes current and former usage)"; among its other names, "can be used for"), and the OBO ontologies' objective specification is "A directive information entity [thing] that describes an intended process endpoint" (IAO_0000005, https://www.ebi.ac.uk/ols4). HAS_PURPOSE, "is meant to achieve", is Wikidata's "has goal": a mission's "objective" is a purpose, and what something is used to study, or what a method "allows for", is a use, which HAS_PURPOSE doesn't hold. Coining a "use" predicate for one record would tailor the schema to it, so what the structure function "allows for" (the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3") is a final left-out, by rule 8 of *What counts as a fact*, *A study a record tells* ("the study's aim and its method are facts of the record's dataset … The rest of the study is not": what the method allows for is a detail the study gives of its method, beside the method itself, "structure function (SF)", already a ground truth triple). Its row of annotations/pending_triples.csv, "structure function (SF)" (Algorithm) HAS_PURPOSE "ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived" (Purpose), is deleted, and the file keeps its header only. The record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid"'s "used to calculate" stays left out as a purpose (rule 16, annotations/left_out.md), as this reading says.

### Quoted for us

- entity class CelestialBody: a natural object in space, or a kind of such objects, e.g. Vesta; active galactic nuclei
- predicate HAS_TARGET: is about, or studies, this CelestialBody
- entity class Mission: a named effort to collect data, from space, from the air, on water or on the ground, e.g. Rosetta; BARREL
- entity class Platform: a craft or station that carries Instruments, in space, in the air, on water or on the ground: a spacecraft, an aircraft, a balloon, a ship or a ground station, e.g. Aqua; Voyager 1
- predicate USED_TO_STUDY -> HAS_PURPOSE: The subject (a mission, instrument, program or dataset) is designed or used to investigate, characterize or trace the object, a scientific phenomenon or process.
- predicate HAS_OBJECTIVE -> HAS_PURPOSE: The subject (a mission, campaign, project or set of researchers) aims to achieve, study or address the object, a scientific goal, question or problem.
- Writing a classed triple, rule 12: The subject instance is what the sentence is about, which isn't always the title.
- Writing a classed triple, rule 19: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 19: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.
- Writing a classed triple, rule 22: A list: one ground truth triple per item. Apply rule 19 first. Then put one item alone in the list's place (the subject or the object), with the words the items share copied onto it. Each item is now one thing, so shared words that agree with the number of items are put in the singular to agree with one item ("channels" → "channel"; "are" → "is"); each item's own words stay as written ("oceans").
- Writing a classed triple, rule 22: Describing words joined by "and" or a comma. Ask: can one of the things they describe have all the describing words at once? 1. Yes: keep them whole, in one ground truth triple. 2. No: split them, one ground truth triple per describing word.
- Writing a classed triple, rule 22: Suppose: a record says Aqua was launched "to study the global dynamics of the Earth atmosphere, land and oceans". Then: rule 19 first gives Aqua HAS_TARGET "Earth"; then three ground truth triples: Aqua HAS_PURPOSE "study the global dynamics of the atmosphere", "study the global dynamics of the land", and "study the global dynamics of the oceans".

### Consequences

#### Option 1: Keep it as it is

- Nothing changes in the ground truth triples listed under Affects, the annotation guidelines, or the translation table.
- A search of the knowledge graph for what studies the Earth's atmosphere has to search inside the words of purposes.

#### Option 2: What something studies apart from its purpose

- The translation table's [row](../docs/terminology.md#8-the-pipeline) for USED_TO_STUDY (current schema) changes to the new predicate.
- An annotator, and the model, must tell an aim from a thing studied in each sentence; "to study the global dynamics of the Earth atmosphere" is both.

### Affects

- record at pool position 0: 3122be4c-b9d0-4cc9-b6d3-9b96c6e743da
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 0: "NASA Standards and and Technical Assistance Resource Tool" (WebTool) HAS_PURPOSE "make it simpler for technical people to access NASA technical information quickly and conveniently" (Purpose)
- classed triple of the record at pool position 2: "series of screens" (Algorithm) HAS_PURPOSE "alleviate errors" (Purpose)
- classed triple of the record at pool position 2: "series of screens" (Algorithm) HAS_PURPOSE "flag uncertain snow cover detections" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the atmosphere" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the land" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the oceans" (Purpose)
- classed triple of the record at pool position 4: "modified nonlinear SST algorithm" (Algorithm) HAS_PURPOSE "provide continuity of SST derived from heritage and current NASA sensors" (Purpose)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_PURPOSE "determine the ensemble variability properties of two serendipitously selected samples" (Purpose)
- classed triple of the record at pool position 18: "Climate Modeling Grid (CMG)" (Grid) HAS_PURPOSE "use in climate simulation models" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "study electron losses from Radiation Belts" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "augment the Radiation Belt Storm Probes, RBSP, mission" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "providing measurements of the spatial variations of electron precipitation from the radiation belts" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "providing measurements of the temporal variations of electron precipitation from the radiation belts" (Purpose)
- classed triple of the record at pool position 19: "X-ray spectrometer" (Instrument) HAS_PURPOSE "measure the bremsstrahlung X-rays produced by precipitating relativistic electrons as they collide with neutrals in the atmosphere" (Purpose)
- classed triple of the record at pool position 19: "DC magnetometer" (Instrument) HAS_PURPOSE "measure ULF-timescale variations of the magnetic field" (Purpose)
- classed triple of the record at pool position 19: "2013 balloon campaign" (Campaign) HAS_PURPOSE "maintain an array with about five payloads spread across about six hours of magnetic local time, MLT, in the region that magnetically maps to the radiation belts" (Purpose)
- classed triple of the record at pool position 19: "2014 balloon campaign" (Campaign) HAS_PURPOSE "maintain an array with about five payloads spread across about six hours of magnetic local time, MLT, in the region that magnetically maps to the radiation belts" (Purpose)
- classed triple of the record at pool position 25: "Satellite Needs Working Group (SNWG)" (Organization) HAS_PURPOSE "identifying observation needs across U.S. civilian federal agencies" (Purpose)
- classed triple of the record at pool position 25: "Satellite Needs Working Group (SNWG)" (Organization) HAS_PURPOSE "addressing observation needs across U.S. civilian federal agencies" (Purpose)
- translation table row: predicate USED_TO_STUDY
- translation table row: predicate HAS_OBJECTIVE
- ground truth schema entry: entity class Purpose
- ground truth schema entry: predicate HAS_PURPOSE
- rule: Writing a classed triple, rule 12
- rule: Writing a classed triple, rule 19
- rule: Writing a classed triple, rule 22

## Q10: Fields of science: which list of disciplines should we follow?

- status: open
- priority: medium
- question kind: schema entry
- in short: the ground truth schema's Discipline, and its Technique for radio science data, the translation table's rows for Method and Topic, and a reference list of disciplines

### The question

Our schema has an entity class Discipline, a field of science, and a predicate HAS_DISCIPLINE that joins a dataset to one (both defined below). The record below, a Rosetta radio science dataset, says "This is a Rosetta Radio Science data set"; we write "Radio Science" not as a Discipline but as a Technique, a way of making measurements, because the Planetary Data System files radio science as a type of instrument, not as a field of science. So the records we have annotated so far name no Discipline, and before more do, we would like to know:

Which list of fields of science should we follow, so that a record's words can be checked against it? We know of three: the divisions of NASA's Science Mission Directorate, among them Earth Science, Planetary Science, Astrophysics and Heliophysics (https://science.nasa.gov/about-us/); the Disciplines list of NASA's Global Change Master Directory (GCMD), which goes beyond Earth science, with fields such as Astronomy, Planetary Science, Solar Physics and Agricultural Sciences (https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/discipline/?format=csv); and the subject categories of NASA's Technical Reports Server (NTRS), such as "Space Sciences" and "Lunar And Planetary Science And Exploration". Which is the right list for this catalog? And is a subject a dataset addresses, such as "agriculture" or "ecosystem interaction", a field of science too? GCMD keeps the two apart: its Disciplines list has "Agricultural Sciences", while its Science Keywords have "Agriculture" as a subject.

### Example record

- record id: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- pool position: 1
- title: ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0
- notes: This is a Rosetta Radio Science data set, collected during the COMET ESCORT 4 phase 2015-10-22 to 2015-12-31. It is a Global Gravity measurement at the comet 67P and covers the time 2015-11-01T19:58:35.000 to 2015-11-02T04:59:27.000.
- source text: This is a Rosetta Radio Science data set
- classed triple: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) USES_TECHNIQUE "Radio Science" (Technique)

### Ground truth schema

- entity class Discipline: a field of science
- predicate HAS_DISCIPLINE: belongs to this Discipline
- entity class Technique: a way of making measurements, e.g. radio science
- predicate USES_TECHNIQUE: was collected using this Technique

### Options

#### Option 1: Keep each record's own words

A Discipline is written in the record's own words, and any subject a dataset addresses (such as "agriculture") counts as a Discipline.

#### Option 2: Disciplines from a reference list

A Discipline is written as the value of the list your answer names that the record's words mean; a subject that is not on the list (such as "agriculture") is not a Discipline.

### My current reading

Option 1, for now, since no record we have annotated names a field of science yet. We would choose option 2 if your answer gives a list that covers the catalog.

### My notes

Checked against sources on 2026-10-30: the Planetary Data System files RSI as an instrument ("ROSETTA RADIO SCIENCE INVESTIGATION", instrument type "RADIO SCIENCE"; ESA catalog files, https://archives.esac.esa.int/psa/ftp/INTERNATIONAL-ROSETTA-MISSION/RSI/RO-C-RSI-1-2-3-ESC4-1149-V1.0/CATALOG/). Radio science is not one of the PDS discipline nodes, and NASA's Science Mission Directorate has five divisions (Astrophysics, Biological and Physical Sciences, Earth Science, Heliophysics, Planetary Science), none of them radio science: evidence that it is a technique rather than a discipline (strong secondary).

The example is the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0". The model extracts classed triples with the current schema. Before they are compared with the ground truth, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names. The ground truth's two Algorithms so far are those of the records "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" and "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (not listed under Affects: no option changes them).

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) is the old (a); their (b) holds the old (b) and (c); their (c) the old (d) and (e). What the expert's answers mean for the current schema's Method and Topic (their rows of the translation table) we settle ourselves.

- (a) Is "RSI" in a title like this one the name of an instrument? Our reading (not checked in a source): radio science measures the spacecraft's own radio signal, as received on Earth, so the "instrument" is the spacecraft's radio system together with the ground stations. Is it right to call RSI an Instrument?
- (b) Is "Radio Science" a field of science (like oceanography), or a technique (a way of measuring, used in several fields)?
- (c) If it is a technique: should the ground truth have an entity class for techniques, apart from Algorithm ("a method applied to data to compute a result") and Discipline? The [model](../docs/terminology.md#8-the-pipeline) that reads the records has an entity class Method that also covers ways of collecting or sending data (an operating mode; our example: radio occultation, an observing technique), and the translation table (quoted below) says it means Algorithm. Is such a technique an Algorithm, or something else?
- (d) The model's Topic covers any subject a dataset addresses ("agriculture", "AGN", "ecosystem interaction"), and the translation table says it means Discipline. Is a subject like these a Discipline, a field of science?
- (e) Which list of disciplines should the ground truth follow, so that a record's words can be checked against it? The one we know of is the divisions of NASA's Science Mission Directorate, among them Earth Science, Planetary Science, Astrophysics and Heliophysics (https://science.nasa.gov/about-us/). Is that the right list for this catalog, or is another one used?

The question's context, as it was: The record doesn't say what "RSI" stands for, and the annotation guidelines don't let us write what an unexplained abbreviation stands for, so the object instance is "RSI", as written. "Radio Science" is the only Discipline we have written so far. The translation table names one entity class of the ground truth schema for each of the model's, whatever the record: so every Method the model finds is judged as an Algorithm, and every Topic as a Discipline. The two Algorithms we have written so far are methods applied to data.

The options as they were worded before 2026-10-26: option 1, ""RSI" is an Instrument, and "Radio Science" a Discipline; the model's Method means Algorithm, and its Topic means Discipline; a Discipline is written in the record's own words."; option 2, "An entity class of its own for a technique of measuring (for example, Technique), and a predicate joining a Dataset to it; "Radio Science" moves there, "RSI" stays an Instrument, and the model's Method means the new entity class where what it names is a technique."; option 4, "A Discipline's object instance is the value of the list your answer to (e) names that the record's words mean; a subject that is not on the list (a Topic such as "agriculture") is not a Discipline, and the model's Topic means nothing in the ground truth schema, or an entity class of its own for subjects."

Decided on 2026-10-31, from the sources checked on 2026-10-30 (above): the old (a) and (b) are settled, so they are no longer asked. (a): the record doesn't say what "RSI" stands for, so by rule 1 of *What counts as a fact* ("never write down what an unexplained code or abbreviation stands for. This includes its entity class") it gives no ground truth triple; the ground truth no longer has "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument). annotations/left_out.md notes it, with the Planetary Data System's INSTRUMENT_ID = RSI, INSTRUMENT_TYPE = RADIO SCIENCE. (b): radio science is a technique, not a field of science: the Planetary Data System has no radio science discipline node (its six are "Atmospheres, Geosciences, Cartography and Imaging Sciences, Planetary Plasma Interactions, Ring-Moon Systems, and Small Bodies", https://pds.nasa.gov/home/about/), files "RADIO SCIENCE" as an INSTRUMENT_TYPE, and sends radio science data to the node of the target; NASA's Science Mission Directorate's five divisions don't include it. So the ground truth schema has a new entity class Technique ("a way of making measurements, e.g. radio science") and a new predicate USES_TECHNIQUE ("was collected using this Technique"), the old option 2, and the record now has "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) USES_TECHNIQUE "Radio Science" (Technique), in place of "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_DISCIPLINE "Radio Science" (Discipline). Of the old option 3, only its first half holds: "RSI" is no longer written as an Instrument, and nothing is written in its place. What the Technique means for the current schema's Method (its row of the translation table, now Algorithm) we settle ourselves. Rule 12's example in the annotation guidelines now says USES_TECHNIQUE "Radio Science" (Technique).

Taken out of the expert's view on 2026-10-31, as questions we can settle from sources; kept here word for word. The expert's question is the old (c), without its letter. The title was "Radio science, techniques and fields of science: is RSI an Instrument, is Radio Science a Discipline, and which list of disciplines?". The options were renumbered: the old option 4 is now option 2, and says "your answer" where it said "your answer to (c)"; the new option 1 replaces the old option 1.

Changed in the expert's view on 2026-10-31 (the research of 2026-10-31 on NASA's reference lists), so that it names the candidate lists we found; the question's second paragraph was, word for word: "Which list of fields of science should we follow, so that a record's words can be checked against it? The one we know of is the divisions of NASA's Science Mission Directorate, among them Earth Science, Planetary Science, Astrophysics and Heliophysics (https://science.nasa.gov/about-us/). Is that the right list for this catalog? And is a subject a dataset addresses, such as "agriculture" or "ecosystem interaction", a field of science too?"

Checked on 2026-10-31, against part of the reason for Technique (docs/improvements.md, B4): PDS4's own search facet `discipline_name` does allow "Radio Science": "The attribute pds:discipline_name must be equal to one of the following values 'Atmospheres', 'Fields', 'Flux Measurements', 'Geosciences', 'Imaging', 'Particles', 'Radio Science', 'Ring-Moon Systems', 'Small Bodies', 'Spectroscopy'" (the PDS4 schematron, IM 1.23.0.0, https://pds.nasa.gov/datastandards/schema/released/pds/v1/PDS4_PDS_1N00.sch), and its node names still include "Radio Science", though no such node exists today. But the facet lists "Radio Science" beside "Imaging" and "Spectroscopy", so it mixes fields with techniques, and radio science still fits Technique by our definitions; the decision stands. The candidate lists: GCMD's Disciplines (96 entries with their subdisciplines, e.g. "ASTRONOMY" with "RADIO ASTRONOMY", "PLANETARY SCIENCE" with "SMALL BODIES"; Keyword Version 25.1; which metadata uses it today was not checked) and NTRS's subject categories (10 divisions and 76 categories in the NASA STI Scope and Subject Category Guide, strong secondary; NTRS files Rosetta's radio science papers under "Space Sciences" and "Lunar And Planetary Science And Exploration"). A discipline list belongs to docs/improvements.md, *Linking subject instances and object instances to reference lists* (080).

- The question's opening, as it was: The example is a Rosetta radio science dataset: its title has "RSI", and its notes say "This is a Rosetta Radio Science data set". We wrote "RSI" as the Instrument that collected the data, and "Radio Science" as the dataset's Discipline, a field of science (both defined below). We are not sure about either. We would like to know:
- (a) Is "RSI" in a title like this one the name of an instrument? The record doesn't say what "RSI" stands for, so we write it as it is. Our reading, not checked against a source: radio science measures the spacecraft's own radio signal, as received on Earth, so the "instrument" is the spacecraft's radio system together with the ground stations. Is it right to call RSI an Instrument?
- (b) Is "Radio Science" a field of science (like oceanography), or a technique, a way of measuring used in several fields? If a technique: should techniques of collecting data (radio science, radio occultation) be a kind of thing of their own, apart from an Algorithm, which we keep for a method applied to data to compute a result?
- The example showed the source text "RSI" and the classed triples "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument) and "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_DISCIPLINE "Radio Science" (Discipline), and the ground truth schema's Instrument and Algorithm (now quoted for us below).
- Option 1, "Keep it as it is", as it was: "RSI" is an Instrument, and "Radio Science" a Discipline, written in the record's own words; a technique counts as an Algorithm, and any subject a dataset addresses as a Discipline.
- Option 2, "A technique is its own entity class", as it was: A new entity class for a technique of measuring, and a predicate joining a dataset to it; "Radio Science" moves there, and "RSI" stays an Instrument.
- Option 3, "No instrument for radio science", as it was: "RSI" is written as something other than an Instrument (for example, the name of the investigation), if radio science has no instrument of its own.
- Option 4, "Disciplines from a reference list", as it was: A Discipline is written as the value of the list your answer to (c) names that the record's words mean; a subject that is not on the list (such as "agriculture") is not a Discipline.
- My current reading, as it was: Option 1, for now, since the record gives no more than the code and the words "Radio Science", and every Algorithm and Discipline we have written so far fits its definition. Your answers to (a) and (b) decide options 2 and 3; your answer to (c) decides option 4.
- Option 1's consequences, as they were: Nothing changes in the ground truth triples listed under Affects, or in the translation table. Every radio science dataset of the catalog gets an "instrument" named by the title's code, and the field "Radio Science"; a search of the knowledge graph for the fields of science finds Radio Science among them. A technique or a topic the model extracts is compared as an Algorithm or a Discipline; if the expert's answers say they aren't, those classed triples are counted wrong, or counted right when they shouldn't be.
- Option 2's consequences, as they were: The ground truth triple with HAS_DISCIPLINE "Radio Science" changes, and the ground truth schema gets a new entity class and predicate. The row for the current schema's Method changes (to the new entity class where what it names is a technique), and is checked again.
- Option 3's consequences, as they were: The ground truth triple ACQUIRED_BY_INSTRUMENT "RSI" changes, and a new entity class or predicate may be needed for an investigation.
- Option 4's consequences also had: The ground truth triple HAS_DISCIPLINE "Radio Science" is checked against the list.

### Quoted for us

- entity class Instrument: a device that takes measurements
- entity class Algorithm: a method applied to data to compute a result, e.g. series of screens; modified nonlinear SST algorithm
- predicate ACQUIRED_BY_INSTRUMENT: was collected by this Instrument
- predicate PRODUCED_USING_ALGORITHM: was made or detected by applying this Algorithm
- entity class Method -> Algorithm: A technique, procedure, operating mode, or analytical approach used to acquire, transmit, or analyze data.
- entity class Topic -> Discipline: A subject area or theme, such as agriculture, AGN, or ecosystem interaction, that a dataset or study addresses.
- predicate HAS_DISCIPLINE -> HAS_DISCIPLINE: The subject (a set of observations or data) belongs to the object, a scientific discipline or category.
- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or abbreviation stands for.
- Writing a classed triple, rule 11: Subject instance and object instance: the record's own words, as written.
- Writing a classed triple, rule 14: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.

### Consequences

#### Option 1: Keep each record's own words

- Nothing changes in the ground truth or in the translation table.
- A topic the model extracts (its Topic, such as "agriculture") is compared as a Discipline; if your answer says such subjects aren't fields of science, those classed triples are counted right when they shouldn't be.
- One field of science may be written in different words in different records, so a search of the knowledge graph by field has to know every wording.

#### Option 2: Disciplines from a reference list

- A new exception to rule 11 of "Writing a classed triple" (quoted above, for us), in the annotation guidelines and in the copy of the rules the model follows, which both change.
- The row for the current schema's Topic changes: to (none), or to a new entity class for subjects.
- Every record names a field of science the same way, so a search of the knowledge graph by field needs one value.
- No ground truth triple has a Discipline yet, so none changes now.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) USES_TECHNIQUE "Radio Science" (Technique)
- classed triple of the record at pool position 25: "Sentinel-1 radar observations" (Dataset) USES_TECHNIQUE "radar" (Technique)
- translation table row: entity class Method
- translation table row: entity class Topic
- translation table row: predicate HAS_DISCIPLINE
- ground truth schema entry: entity class Discipline
- ground truth schema entry: predicate HAS_DISCIPLINE
- ground truth schema entry: entity class Technique
- ground truth schema entry: predicate USES_TECHNIQUE
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 11
- rule: Writing a classed triple, rule 14
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which a list of disciplines to follow would change

## Q11: What counts as an area the data cover: "Land", and sorts of surface?

- status: open
- priority: medium
- question kind: schema entry
- in short: the ground truth schema's SpatialExtent and HAS_SPATIAL_COVERAGE, and rule 19 of *Writing a classed triple* in the annotation guidelines

### The question

Our schema has an entity class SpatialExtent for the area the data cover, all of a body or part of it, and a dataset HAS_SPATIAL_COVERAGE such an area (both defined below). When a word in a title or a quantity names such an area, we take it out and write it as a fact of its own; a word of any other sort stays where it is. The example is a dataset of "Land Aerosol Optical Depth": we took "Land" out as the area the data cover, and kept "Aerosol Optical Depth" as the quantity measured. We are not sure that is right:

- (a) Is "Land" here an area the data cover, the land surfaces of the Earth as against the oceans? Or is "Land Aerosol Optical Depth" one quantity, the aerosol optical depth over land, which should stay whole? Or does "Land" say what sort of surface the method that computes the product (MAIAC, named in the notes) is made for, so that it stays in the quantity's words? What your answer can still change: we know the method also works over water (its user guide), and we keep the record's word "Land" as an area unless you tell us that the field reads "Land Aerosol Optical Depth" as the name of one quantity.
- (b) In general: should an area the data cover be only a region of a body (the Arctic, a pole, the whole body), or also a sort of surface the data are limited to (land, ocean, sea ice)?

### Example record

- record id: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- pool position: 6
- title: MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid
- notes: The Moderate Resolution Imaging Spectroradiometer (MODIS) Near Real Time (NRT) Combined Terra and Aqua Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product (MCD19A2N) produced daily at 1 kilometer (km) pixel resolutions. The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product.
- source text: Land Aerosol Optical Depth
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_COVERAGE "Land" (SpatialExtent)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity)

### Ground truth schema

- entity class SpatialExtent: an area the data cover, of the CelestialBody they are about: all of it (global) or part of it (e.g. Arctic; south pole of Mars; a country, when the data cover it)
- predicate HAS_SPATIAL_COVERAGE: covers this SpatialExtent

### Options

#### Option 1: Keep them as we wrote them

"Land" (in the example) is an area the data cover, a fact of its own.

#### Option 2: Only regions of a body are areas

An area is only a region of a body, or the whole of it. "Land Aerosol Optical Depth" stays whole, as the quantity measured.

#### Option 3: Name sorts of surface in the definition

The definition of an area the data cover says that a sort of surface the data are limited to (land, ocean, sea ice) is an area too, and it is taken out like any area.

### My current reading

Undecided. For "Land", we lean towards option 3: it says which part of the Earth the data cover, which is what a search would ask.

### My notes

Every ground truth triple with HAS_SPATIAL_COVERAGE so far is listed under Affects: "Global" (the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0"), "global" (the records "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" and "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0"), and "Land" and "Global" (the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid", the example), and "Global" (the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006"; both "Global" since 2026-10-30). The count of the recurring sentence is over 020's records.jsonl (36,406 records). Until the answers, the ground truth stays as written (option 1). Rule 19 of *Writing a classed triple* now records our reading of a word naming a kind of ground or water: it is an area the data cover when "the [rest] of the [word]" is false ("the aerosol optical depth of the land" is false, because the aerosols are in the air), so "Land" stays taken out in the example; if the answers say otherwise, rule 19, the model's copy of the rules, and the ground truth triples under Affects change with them.

Checked on 2026-10-30: MAIAC also retrieves aerosol optical depth over inland, coastal and open-ocean water (MCD19A2 has "Over water" layers), so the title's "Land" names the product suite; the ground truth keeps "Land" as the record's words (decided on 2026-10-31, kept). Source: the MAIAC Collection 6.1 user guide (Lyapustin and Wang, LP DAAC, https://lpdaac.usgs.gov/documents/1500/MCD19_User_Guide_V61.pdf), section 3.2: "MAIAC processing is limited to global land tiles and land-containing ocean tiles (green and light blue colors in Fig. 1). Over inland, coastal and open ocean waters, MAIAC reports AOD, fine mode fraction, and spectral reflectance of underlight (water-leaving reflectance)"; that "Land" names the product suite is my reading.

Added on 2026-10-31: the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" now has "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_COVERAGE "Polar" (SpatialExtent), taken out of the title's "Polar-Gridded" by rule 19, as "Global" was (its data cover only latitudes poleward of 50 degrees, NSIDC's user guide; see Q1); it is under Affects.

How the translation table is used: the [model](../docs/terminology.md#8-the-pipeline) extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with the ground truth, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names. A row that names (none) says nothing in the ground truth schema means the same: a classed triple that uses it can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only. The current schema's SpatialCoverage and HAS_SPATIAL_COVERAGE translate into SpatialExtent and HAS_SPATIAL_COVERAGE, so the answer also decides what an extracted triple with them is compared with.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) is the old (b), their (b) the old (c). The old (a), on "Global Gravity", is the same doubt as Q3's (c) (whether "Global Gravity" names a kind of measurement), so the expert reads it there only; what "Global" means at a comet we settle once Q3's (c) is answered: if "Global Gravity" is a name as a whole, "Global" is no area. The example no longer shows the source text "Global 1km SIN Grid" (settled, see the context below).

- (a) The record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" says "It is a Global Gravity measurement at the comet 67P". We wrote "Global" as the area the data cover (all of the comet 67P). At a comet, what would "Global" mean: the whole comet, or something else? Or is "Global Gravity" the name of one sort of radio science measurement, as a whole, so that "Global" is no area at all? (Other records of the catalog have the same sentence with "Phobos Gravity", "Occultation" or "Solar Conjunction" in its place: see below.)
- (b) The example below is a dataset of "Land Aerosol Optical Depth". We took "Land" out as the area the data cover ("MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_COVERAGE "Land" (SpatialExtent)), and kept "Aerosol Optical Depth" as the quantity measured. Is "Land" (the land surfaces of the Earth, as against the oceans) an area in the sense of SpatialExtent, "part of" the Earth? Or is "Land Aerosol Optical Depth" one quantity, the aerosol optical depth over land, which should stay whole? Or does "Land" say what sort of surface the method that computes the product (MAIAC) is made for, so that it stays in the quantity's words as a qualifier of another sort (rule 19 of *Writing a classed triple*: "any other kind")?
- (c) In general: should SpatialExtent hold only a region of a body (the Arctic, a pole, the whole body), or also a sort of surface (land, ocean, sea ice) that the data are limited to?

The question's context, as it was: The areas we have written so far are "Global" (the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0"), "global" (the records "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" and "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0"), and our draft "Land" (the example below, which question (b) is about).

Settled, so not asked here: the example's title ends in "Global 1km SIN Grid". Corrected on 2026-10-30: no source calls "Global 1km SIN Grid" the grid's name, and the sources treat "Global" as the product's worldwide coverage (NASA LAADS DAAC on the MODIS tiles: "Each tile has fixed Earth-locations covering an area of approximately 1200 x 1200 km (10 x 10 degrees at the equator)"; MODLAND calls the grid the "Sinusoidal Tile Grid" (https://modis-land.gsfc.nasa.gov/MODLAND_grid.html), and NASA CMR names its tiling system "MODIS Tile SIN"; CMR gives these products global spatial coverage; 8 of the catalog's 384 "SIN Grid" titles have no "Global"), so the example now has HAS_SPATIAL_COVERAGE "Global" as well as "Land" (rule 19). As checked on 2026-10-25, before the correction: "SIN Grid" is the MODIS sinusoidal grid, and "Global 1km SIN Grid" is the standard end of the titles of the MODIS products made on it, so "Global" there was read as naming the grid's worldwide tiling, not the area this dataset covers (NASA LAADS, the MCD19A2 product page, https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MCD19A2; NASA MODAPS, MCD19A2N, https://modaps.modaps.eosdis.nasa.gov/services/about/products/c61-nrt/MCD19A2N.html). So we had written no area "Global" for it; since 2026-10-30 we do. A "global" written as a word of its own ("This global Level-2 (L2) data set") we are sure of; the three words above we are not.

The sentence of the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" recurs across the catalog. We counted it in the catalog's 36,406 records: "It is a Global Gravity measurement" in 2,835 records (2,442 of them "at the comet 67P"), "It is a Occultation measurement" in 439, "It is a Solar Conjunction measurement" in 240, and "It is a Phobos Gravity measurement" in 9. Since "Phobos Gravity" sits beside "Global Gravity", our reading is that the word before "Gravity" may say which gravity measurement it is, not an area; but we don't know.

The options and current reading as they were worded before 2026-10-26: option 1, ""Global" (at the comet 67P) and "Land" (in the example) are areas the data cover, each a fact of its own."; option 2, "SpatialExtent holds only a region of a body, or the whole of it. "Land Aerosol Optical Depth" stays whole, as the quantity measured, since rule 19 of *Writing a classed triple* keeps a qualifier that is no area in the instance; "Global Gravity" stays whole too, if the answer to (a) is that it names a measurement."; option 3, "The definition of SpatialExtent says that a sort of surface the data are limited to (land, ocean, sea ice) is an area too, and rule 19 of *Writing a classed triple* takes it out like any area."; current reading, "Undecided. For "Land", we lean towards option 3: it says which part of the Earth the data cover, which is what a search would ask. For "Global Gravity", we lean towards keeping it whole, since "Phobos Gravity" in other records reads like the same sort of title; your answer to (a) decides it."

Changed on 2026-10-31: the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" no longer has "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_SPATIAL_COVERAGE "Global" (SpatialExtent): "Global Gravity" is the archive's name for a mode of measurement, kept whole (decided on 2026-10-31, Q3's My notes), and the record now has "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_VARIABLE "Global Gravity" (Variable). So the record and its two classed triples are no longer under Affects, and the question no longer names "Global" at a comet; its title was "Q11: What counts as an area the data cover: "Global" at a comet, and "Land"?". Option 1's and option 2's consequences said, word for word: "If "Global Gravity" is the name of one sort of measurement (Q3's (c)), the area "Global" is a [fact](../docs/terminology.md#2-triples) the record doesn't state, and the 2,835 records with this sentence would each get it." and "The record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" loses HAS_SPATIAL_COVERAGE "Global", and its HAS_MEASUREMENTS_OF "Gravity" becomes "Global Gravity", if the answer to Q3's (c) says so.". The "Phobos Gravity" we didn't know (above) is checked: Mars Express's measurement of Phobos's mass from close flybys (Q3's My notes). What "Global" means at a comet, the field of the whole nucleus, stays my reading; no Rosetta document defines it.

Checked on 2026-10-31, the reading above that the title's "Land" names the product suite: no source says so in words. What the sources show is that "Land" is the MODIS land discipline's naming: the MODIS Land Team lists MAIAC, LP DAAC (the Land Processes archive) holds it, its user guide calls its grid choice "a tradeoff made by the MODIS land team for the global data processing" (https://lpdaac.usgs.gov/documents/1500/MCD19_User_Guide_V61.pdf, section 3.1), and its sibling product is the "Land Surface BRF"; it also retrieves over water (above). Strong secondary, so it stays my reading; the ground truth keeps "Land" (rule 1 of *What counts as a fact*), and the expert's (a) now says what an answer can still change (the inventory of 2026-10-31, as research B14 narrowed other questions).

Checked on 2026-10-31, for the expert's (b) (the research of 2026-10-31 on NASA's metadata): GCMD's Locations list, which says where data are, has sorts of surface as locations: under GEOGRAPHIC REGION, "GLOBAL LAND", "GLOBAL OCEAN" and "POLAR"; under VERTICAL LOCATION, "LAND SURFACE" and "SEA SURFACE" (KMS `locations`, Keyword Version 25.1). That supports reading "Land" and "Polar" as areas (option 3), as the ground truth does now; for Q1, "POLAR" supports "Polar" in "Polar-Gridded" as an area. CMR's own record of MCD19A2N gives its location as GLOBAL, not GLOBAL LAND: an outside fact, for docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080); it doesn't override the record's "Land" (rule 1 of *What counts as a fact*).

### Quoted for us

- entity class PhysicalQuantity: a bare property that can be measured, whatever method measures it, e.g. temperature; gravity; sea surface temperature; snow cover; not a form the data take, such as images, image cubes, spectra or maps (a SpatialRepresentation)
- entity class CelestialBody: a natural object in space, or a kind of such objects, e.g. Vesta; active galactic nuclei
- predicate HAS_MEASUREMENTS_OF: holds measurements of this PhysicalQuantity
- predicate HAS_TARGET: is about, or studies, this CelestialBody
- entity class SpatialCoverage -> SpatialExtent: The geographic or sky extent covered by a dataset or observation, such as global, a swath width, or a number of square degrees or areas.
- predicate HAS_SPATIAL_COVERAGE -> HAS_SPATIAL_COVERAGE: The subject (a dataset or survey) covers the object, a geographic region, latitude range, area extent or coverage descriptor.
- Writing a classed triple, rule 19: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 19: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.

### Consequences

#### Option 1: Keep them as we wrote them

- Nothing changes in the ground truth triples listed under Affects.
- SpatialExtent holds both regions and sorts of surface (land); its definition would say so.

#### Option 2: Only regions of a body are areas

- The ground truth triples of the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" become one: HAS_MEASUREMENTS_OF "Land Aerosol Optical Depth", with no HAS_SPATIAL_COVERAGE (rule 19 of *Writing a classed triple* keeps a qualifier that is no area in the instance).
- A search for land-only data has to look inside the quantities' words.

#### Option 3: Name sorts of surface in the definition

- The ground truth schema's definition of SpatialExtent changes, and the rows of the translation table into it are checked again.
- The model's copy of the rules (rule 19 of *Writing a classed triple*) says the same, so extraction takes "Land" out too.

### Affects

- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_SPATIAL_COVERAGE "Polar" (SpatialExtent)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_SPATIAL_COVERAGE "global" (SpatialExtent)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_COVERAGE "global" (SpatialExtent)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_COVERAGE "Land" (SpatialExtent)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_COVERAGE "Global" (SpatialExtent)
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_SPATIAL_COVERAGE "Global" (SpatialExtent)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) HAS_SPATIAL_COVERAGE "Global" (SpatialExtent)
- classed triple of the record at pool position 18: "Climate Modeling Grid (CMG)" (Grid) HAS_SPATIAL_COVERAGE "globe" (SpatialExtent)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_SPATIAL_COVERAGE "from -64 to 80 degrees" (SpatialExtent)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_SPATIAL_COVERAGE "near-global" (SpatialExtent)
- translation table row: entity class SpatialCoverage
- translation table row: predicate HAS_SPATIAL_COVERAGE
- translation table row: predicate HAS_PROPERTY
- ground truth schema entry: entity class SpatialExtent
- ground truth schema entry: predicate HAS_SPATIAL_COVERAGE
- rule: Writing a classed triple, rule 19
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules (the list of qualifiers taken out, rule 19 of *Writing a classed triple*)

## Q12: What counts as a dataset: inputs named in a record, and archives, catalogs and data products?

- status: open
- priority: medium
- question kind: schema entry
- in short: the ground truth schema's Dataset, for the data a record's dataset is made from and for collections of datasets; four rows of the translation table into Dataset

### The question

Our schema's Dataset is "a set of observations, measurements, or samples" (defined below). Besides each record's own dataset, we have written as Datasets the data it was made from, its parts, and the catalogs it draws on. We are not sure each is a dataset in the sense someone in the field would use. We would like to know:

- (a) The example says its snow index "is derived from radiance data acquired by" MODIS, followed by two DOIs, MYD02HKM and MYD021KM. We wrote one Dataset, "radiance data", with both DOIs. Are these one dataset or two (our reading: two products, at two resolutions)? If two, how should two inputs with the same words be told apart, when the record names them only by their DOIs?
- (b) Is data in the middle of processing a dataset? The record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" says "the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG)", and we wrote "pixels" as a Dataset at processing level "L2". The record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" says "This data set contains Level 2/3 (EDR/RDR) data" and "The RDR data convert the EDR (raw) sensor data", and we wrote "RDR data" and "EDR (raw) sensor data" as two Datasets, each part of the record's dataset, one made from the other. Are such pixels, parts and data products datasets themselves, or should they be written another way?
- (c) Is a collection of data a dataset in the same sense as a set of measurements of the Earth's surface? The record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" is a table of quasars selected from the source catalog "2XMMi-DR3" and matched with "the DR7 edition of the SDSS Quasar Catalog"; we wrote both catalogs as Datasets. Is an astronomical source catalog (a list of objects, each with its measured properties) a dataset? And is a database or archive that holds many datasets the same sort of thing as the datasets it holds, or should the two be kept apart (e.g. so that a search for datasets doesn't return archives)?

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
- predicate COMPUTED_FROM: was made by processing this input

### Options

#### Option 1: Keep them all as Datasets

Every input, part and collection of data named in a record is a Dataset, in the record's words, with the facts the record states about it.

#### Option 2: One input per DOI

When a record names inputs by their DOIs, each DOI is its own Dataset, and the record's words ("radiance data") are written once per DOI.

#### Option 3: Inputs only, no facts about them

Each input stays a Dataset, but we write nothing else about an input that has its own record in the catalog (for example, the instrument that collected it).

#### Option 4: An entity class for collections of datasets

When a record names an archive, a database or a source catalog that holds many datasets, our schema gets an entity class for it, apart from Dataset.

### My current reading

Option 1, for now: it writes what each record states, and every collection of data in the records we have read so far is one set of measurements. Your answer to (a) decides option 2, and your answer to (c) option 4.

### My notes

The example is the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061". The other two inputs are "the L2 pixels" of the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" and "the GRaND epithermal neutron map" of the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0"; every ground truth triple about each of the three inputs is listed under Affects. The record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" names three source catalogs and a file of one (decided 2026-10-25, for us to confirm; confirmed on 2026-10-31, below: a source catalog is data, and "table1.dat" PART_OF its catalog stands); none of the tuning records so far names a database. The search of the old (c) was over the titles of 020's records.jsonl.

Decided on 2026-10-25, for us to confirm: the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" has an input of its own, "MOD11_L2" (its swath product, with its DOI), and the record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" has two parts, "RDR data" and "EDR (raw) sensor data"; their classed triples are listed under Affects. Confirmed on 2026-10-31 (below, for the expert's (b)): published products such as these are datasets.

How the translation table is used: the [model](../docs/terminology.md#8-the-pipeline) extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with the ground truth, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names. A row that names (none) says nothing in the ground truth schema means the same: a classed triple that uses it can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) is the old (a); their (b) holds the old (b) and (f); their (c) the old (d) and (e). Left for us: the old (c), on the epithermal map, which is about our own rule 21 (option 3 stays one of the expert's choices); the rest of the old (d), "table1.dat" and "CDS Catalog J/A+A/536/A84" as Datasets, which follows from the answer to (c); and the doubt in the old (d) about "active galactic nuclei (AGN)" (CelestialBody), a kind of object written with an entity class whose definition is "a natural object in space", which is about our schema's definition, for us to settle (or to ask with Q25).

- (a) The example below says the index it uses "is derived from radiance data acquired by" MODIS, followed by two DOIs, MYD02HKM and MYD021KM. We wrote one Dataset, "radiance data", with both DOIs. Are these one dataset or two (our reading: two products, at two resolutions)? If two, how should two inputs with the same words be told apart, when the record names them only by their DOIs?
- (b) The record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" says "the L2 pixels are binned" into a grid. We wrote "pixels" as a Dataset, at processing level "L2". Is a set of Level 2 pixels a dataset, or just the Level 2 data, unnamed?
- (c) The record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says the counts "were detrended using the GRaND epithermal neutron map". We wrote that map as a Dataset, collected by GRaND. No record of the catalog has "epithermal" in its title (we searched the catalog's titles), so we can't tell whether the map is a dataset of its own; the catalog has other GRaND maps of Vesta (for example, "DAWN GRAND MAP VESTA NEUTRON ABSORPTION V1.0"). The annotation guidelines leave out facts about another dataset, but keep them when the record's dataset is made from it (rule 21 of *Writing a classed triple*), so we kept what collected the map. Is it right to keep the map as an input, with what collected it?
- (d) For someone using this catalog, is an astronomical source catalog (a list of objects, each with its measured properties) a dataset in the same sense as a set of measurements of the Earth's surface? The record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" is a table of 412 quasars selected from the source catalog "2XMMi-DR3" and matched with "the DR7 edition of the SDSS Quasar Catalog", "based on CDS Catalog J/A+A/536/A84 [...] file table1.dat". We wrote the table, the two catalogs, "table1.dat" and "CDS Catalog J/A+A/536/A84" as Datasets, and "active galactic nuclei (AGN)", the kind of object the table is about, as its target: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_TARGET "active galactic nuclei (AGN)" (CelestialBody), although a CelestialBody is "a natural object in space" and AGN are a kind of object. Are these right?
- (e) Is a database or archive that holds many datasets the same sort of thing as one of the datasets it holds, or should the two be kept apart (e.g. so that a search for datasets doesn't return archives)?
- (f) Is a "data product" (e.g. "Level-3 products", "the SST4 product") always a dataset, or sometimes one variable inside a dataset? The record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" says "This data set contains Level 2/3 (EDR/RDR) data", and later "The RDR data convert the EDR (raw) sensor data": we wrote "RDR data" and "EDR (raw) sensor data" as two Datasets, each PART_OF the record's dataset, and "RDR data" (Dataset) COMPUTED_FROM "EDR (raw) sensor data" (Dataset). Are the parts of a dataset datasets themselves, or should they be written another way?

The question's context, as it was: The example below is the one whose input, "radiance data", has the most facts of its own (four, two of them DOIs). COMPUTED_FROM joins what was made to what it was made from. Of the records we have read so far, only the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" names astronomical source catalogs (question (d)); none names a database. The translation table says that the model's Dataset, DataProduct, Catalog and Database all mean the ground truth schema's Dataset.

The options and current reading as they were worded before 2026-10-26: option 1, "Every input named in a record is a Dataset, in the record's words, with the facts the record states about it; the model's Catalog, Database and DataProduct all mean Dataset."; option 3, "Keep each input as a Dataset, but write nothing else about an input that is another dataset of the catalog (its instrument, its processing level). Rule 21 of *Writing a classed triple* now keeps such facts, so it would change."; option 4, "When a record names an archive, a database or a source catalog that holds many datasets, the ground truth schema gets an entity class for it, and the model's Database (and Catalog, if your answer to (d) is no) means it."; current reading, "Option 1, for now: it writes what each record states, as rule 21 of *Writing a classed triple* now does for an input, and every collection of data in the records we have read so far is one set of measurements. Your answers decide whether (a) needs option 2, whether (c) needs option 3, and whether (d) and (e) need option 4."

Checked on 2026-10-31, the doubt left for us on "table1.dat" and "CDS Catalog J/A+A/536/A84" as Datasets: the CDS, which keeps them, says "Each catalogue available at CDS is made of several files stored in a directory", and a J catalogue's "designation maps the reference of the published paper" (CDS, *Standard for Documentation of Astronomical Catalogues*, version 2.0, chapter 2, read through the NAO mirror, http://vizier.nao.ac.jp/doc/catstd-2.htx); the catalogue's ReadMe lists "table1.dat" as the "XMM-Newton sample" (412 rows) and "table2.dat" as the "Swift sample" (http://vizier.nao.ac.jp/ftp/cats/J/A+A/536/A84/ReadMe). So "table1.dat" PART_OF "CDS Catalog J/A+A/536/A84", both Datasets, stands, and the record's "Swift (the latter is not included in this table, notice)" is table2.dat. The doubt about "active galactic nuclei (AGN)" as a target is settled by CelestialBody's definition, "a natural object in space, or a kind of such objects, e.g. Vesta; active galactic nuclei".

Checked on 2026-10-31, for the expert's (c), the astronomy half: a source catalog is data, rows of measured properties of objects in files, issued in releases by one agent: "A new incremental version (2XMMi-DR3) of the second XMM-Newton EPIC Serendipitous Source Catalogue, 2XMM, is being released … FITS and CSV versions of the full 2XMMi-DR3 catalogue" (XMM-Newton News #106, https://heasarc.gsfc.nasa.gov/mail_archive/xmmnews/msg00191.html). That fits W3C DCAT's dataset, "A collection of data, published or curated by a single agent, and available for access or download in one or more representations", not its catalog, "A curated collection of metadata about resources" (https://www.w3.org/TR/vocab-dcat-3/): the word "catalog" means different things in the two fields (my reading). So option 1 holds for source catalogs. For an archive of datasets the standards split: DCAT makes dcat:Catalog a kind of dcat:Dataset, while schema.org keeps DataCatalog, "A collection of datasets", apart from Dataset (https://schema.org/DataCatalog); both give it a class of its own, so option 4 has two standard models if a record names one. The expert's (c) stays for that half.

Checked on 2026-10-31, for the expert's (b): DCAT's notion of a dataset "is broad and inclusive", and data come "in many forms including numbers, text, pixels, imagery" (DCAT 3, above), so published products such as the EDR and RDR data are datasets; data in the middle of one processing step, such as "the L2 pixels", are in W3C PROV's terms something a process uses (https://www.w3.org/TR/prov-o/), which our Dataset ("a set of observations, measurements, or samples") already covers (my reading). Option 1 stays.

### Quoted for us

- entity class Variable: a property narrowed by a method, a band, a threshold, another object or another constraint, e.g. SST4; NDSI; band 31 emissivity; dust fluences at each of twelve mass thresholds
- entity class Identifier: a code that names one thing, or one product line, permanently, e.g. a DOI; MOD11A1
- predicate HAS_DOI: has this Identifier, a Digital Object Identifier
- entity class Dataset -> Dataset: A named collection of data compiled from observations, measurements, experiments, or statistics and distributed as a unit, such as an index, data collection, or instrument time series.
- entity class DataProduct -> Dataset: A specific processed output of data, such as calibrated images, retrieval products, files, or data segments, generated from instrument or model data.
- entity class Catalog -> Dataset: A published, organized list of astronomical sources or objects with their properties, typically derived from a survey or mission.
- entity class Database -> Dataset: An organized collection or repository of data records, sources or proposals that can be stored, queried and accessed.
- Writing a classed triple, rule 11: Subject instance and object instance: the record's own words, as written.
- Writing a classed triple, rule 21: General facts: include them; about another dataset, only when the record links it to the record's dataset by "part of" or "made from".
- Writing a classed triple, rule 21: Another dataset. Include facts about another dataset when the record states a chain of "part of" or "made from" links that connects it to the record's dataset: its parts, what it is part of, what it is made from, and so on through further datasets or variables the record names. Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it. In every case, include the connection the record states (rule 1 of What counts as a fact: only what the record states).
- Writing a classed triple, rule 24: A processing step: output = method(input).

### Consequences

#### Option 1: Keep them all as Datasets

- Nothing changes in the ground truth triples or the rows above.
- Two inputs named by the same words ("radiance data") become one node of the knowledge graph, with both DOIs.
- Facts about an input that has its own record (the epithermal map's instrument) are written in this record too, as rule 21 now allows ("Include facts about another dataset when the record states a chain of "part of" or "made from" links that connects it to the record's dataset").
- An archive and the datasets inside it carry the same entity class, so the knowledge graph can't tell them apart by their entity class.

#### Option 2: One input per DOI

- The record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" gets two inputs, each with one DOI; their instances share the same words, so the ground truth needs a way to tell them apart (for example, the DOI written in the instance), which is a new exception to rule 11 of *Writing a classed triple*.

#### Option 3: Inputs only, no facts about them

- The ground truth triples "GRaND epithermal neutron map" ACQUIRED_BY_INSTRUMENT "GRaND", "radiance data" ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)", and "pixels" HAS_PROCESSING_LEVEL "L2" are left out.
- An annotator, and the model, must know whether an input has its own record, which the record's [text](../docs/terminology.md#1-records-and-their-text) often doesn't say.
- Rule 21 of *Writing a classed triple* and the model's copy of the rules change: they now keep the facts about a dataset the record's dataset is made from, and would leave them out.

#### Option 4: An entity class for collections of datasets

- Archives and datasets are kept apart.
- The ground truth schema gains an entity class, and the rows that point to it are checked again: the current schema's Database, and Catalog if the expert's answer to (c) says a source catalog is no dataset.
- It waits for a tuning record that names one.

### Affects

- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- classed triple of the record at pool position 2: "Normalized Difference Snow Index (NDSI)" (Variable) COMPUTED_FROM "radiance data" (Dataset)
- classed triple of the record at pool position 2: "radiance data" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD02HKM.061" (Identifier)
- classed triple of the record at pool position 2: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD021KM.061" (Identifier)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) COMPUTED_FROM "pixels" (Dataset)
- classed triple of the record at pool position 4: "pixels" (Dataset) HAS_PROCESSING_LEVEL "L2" (ProcessingLevel)
- classed triple of the record at pool position 4: "pixels" (Dataset) ON_GRID "integerized sinusoidal area grid (ISEAG)" (Grid)
- classed triple of the record at pool position 4: "pixels" (Dataset) MAPPED_INTO "equidistant cylindrical" (MapProjection)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) COMPUTED_FROM "GRaND epithermal neutron map" (Dataset)
- classed triple of the record at pool position 5: "GRaND epithermal neutron map" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) COMPUTED_FROM "MOD11_L2" (Dataset)
- classed triple of the record at pool position 7: "MOD11_L2" (Dataset) HAS_DOI "https://doi.org/10.5067/MODIS/MOD11_L2.006" (Identifier)
- classed triple of the record at pool position 7: "MOD11_L2" (Dataset) HAS_SPATIAL_REPRESENTATION "swath" (SpatialRepresentation)
- classed triple of the record at pool position 9: "RDR data" (Dataset) PART_OF "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset)
- classed triple of the record at pool position 9: "EDR (raw) sensor data" (Dataset) PART_OF "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset)
- classed triple of the record at pool position 9: "RDR data" (Dataset) COMPUTED_FROM "EDR (raw) sensor data" (Dataset)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) COMPUTED_FROM "2XMMi-DR3" (Dataset)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) COMPUTED_FROM "DR7 edition of the SDSS Quasar Catalog" (Dataset)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) COMPUTED_FROM "table1.dat" (Dataset)
- classed triple of the record at pool position 12: "table1.dat" (Dataset) PART_OF "CDS Catalog J/A+A/536/A84" (Dataset)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_TARGET "active galactic nuclei (AGN)" (CelestialBody)
- translation table row: entity class Dataset
- translation table row: entity class DataProduct
- translation table row: entity class Catalog
- translation table row: entity class Database
- rule: Writing a classed triple, rule 21
- rule: Writing a classed triple, rule 24

## Q13: What counts as a channel: radio frequency bands and wavelength bands?

- status: open
- priority: medium
- question kind: schema entry
- in short: the ground truth schema's Channel; the translation table's rows for Wavelength and Frequency (current or past schema)

### The question

Our schema's Channel is "a range of wavelengths an Instrument measures separately, e.g. 11 micron channel" (defined below). Every Channel we have written so far is in the example: four infrared wavelength channels that its two sea surface temperature products are computed from. Records also name radio frequency bands (such as L-, S-, X- or Ku-band), and we don't know where those belong. For example, the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" says "Aquarius L-band radiometer Sea Surface Salinity (SSS) retrievals", and we wrote its instrument as "Aquarius L-band radiometer", with the band kept inside the instrument's name. We would like to know:

- (a) Which radio frequency bands occur in the records of this catalog, and what do they describe there: the band an instrument measures in (e.g. a radar or a radiometer), the band a spacecraft sends its data down in, or something else?
- (b) For a radio band that an instrument measures in, is Channel the right entity class, or does a radio band need one of its own? Should "L-band" stay inside the instrument's name, as now, or be a [fact](../docs/terminology.md#2-triples) of its own? And for wavelengths: is every band in which observations are made (e.g. an infrared filter band) a Channel, or only a band the instrument measures separately?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels
- source text: At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4
- classed triple: "skin SST" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple: "skin SST" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)

### Ground truth schema

- entity class Channel: a range of wavelengths an Instrument measures separately, e.g. 11 micron channel

### Options

#### Option 1: Keep Channel narrow, and radio bands inside the Instrument's words

Channel stays a range of wavelengths an instrument measures separately, and a radio band written in an instrument's name stays there.

#### Option 2: Widen Channel to any band of the spectrum

Channel's definition says any band of the spectrum an instrument measures in, radio bands included, and a radio band in an instrument's name ("L-band" in "Aquarius L-band radiometer") becomes a fact of its own.

#### Option 3: An entity class of its own for radio bands

A radio band gets an entity class of its own; Channel stays a range of wavelengths an instrument measures separately.

### My current reading

Option 1 for now: the only radio band we have met so far is inside an instrument's name, and the four channels fit Channel as it is. If radio bands are common in the catalog (a), option 2 or 3, as your answer to (b) says.

### My notes

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0"; the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" has "Aquarius L-band radiometer". A row of the translation table that names (none) says nothing in the ground truth schema means the same: a classed triple that uses it can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only.

Option 2 also means a new exception to the list of rule 19 of *Writing a classed triple*, and telling the step that learns the current schema to keep radio bands apart from rates, so that they get a row into Channel. Option 3: the entity class is one we coin in the ground truth schema, once a tuning record needs it.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The expert's (a) is the old (a); their (b) holds the old (b) and (c). The example no longer shows the source text "the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS" nor the classed triples "mid-infrared 3.95 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) and "mid-infrared 4.05 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument); both are under Affects.

The question as it was: The ground truth schema's Channel is "a range of wavelengths an Instrument measures separately, e.g. the 11 micron channel". The schema the [model](../docs/terminology.md#8-the-pipeline) learned from the catalog's records has two entity classes that hold bands of the spectrum: Wavelength ("A wavelength band or spectral range, such as an infrared filter band, in which observations are made"), which the translation table translates into Channel, and Frequency ("A rate of occurrence, such as daily or weekly, or a radio frequency band, such as S-, X-, or Ku-band"), which it translates into TemporalResolution, which fits only the rates. To decide where bands of the spectrum belong, we need to know:

- (a) Which radio frequency bands occur in the records of this catalog, and what do they describe there: the band an Instrument measures in (e.g. a radar or a radiometer), the band a Spacecraft sends its data down in, or something else?
- (b) For a radio frequency band that an Instrument measures in, is Channel the right entity class, or does a radio band need an entity class of its own? And when a record writes the band as part of the Instrument's words ("Aquarius L-band radiometer", in the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005"), should it stay inside them, as it does now, or be a [fact](../docs/terminology.md#2-triples) of its own?
- (c) Is every wavelength band in which observations are made (e.g. an infrared filter band) a Channel, or only a band the Instrument measures separately?

The question's context, as it was: The example below has every Channel we have written down so far: four wavelength channels its two sea surface temperature products are computed from, two of them "unique to MODIS". The record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" names a radio frequency band inside its Instrument's words: "Aquarius L-band radiometer" keeps "L-band", since rule 19 of *Writing a classed triple* takes a qualifier out of an instance only if it is one of the sorts it lists, and a radio band isn't one. So none of the facts we have written down yet has a radio band as its object.

How the translation table is used: the [model](../docs/terminology.md#8-the-pipeline) extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with ours, each entity class and predicate of that schema is replaced by the one of the ground truth schema its [row](../docs/terminology.md#8-the-pipeline) of the translation table names.

The options as they were worded before 2026-10-26: option 1, ("Channel stays a range of wavelengths an Instrument measures separately; a radio band written in an Instrument's words stays there; the rows stay as they are.").

Checked on 2026-10-31, for the expert's (a): the Aquarius radiometers are "Three L-band microwave polarimetric radiometers … with a center frequency of 1.413 GHz", and its scatterometer "transmits in a protected 1260 MHz frequency" (PO.DAAC, https://podaac.jpl.nasa.gov/aquarius). The frequency is for 080's enrichment, since the record states only "L-band"; it supports keeping "L-band" inside the instrument's name (research G8 of 2026-10-30). The count of "-band" over the induction candidates is still to make.

Checked on 2026-10-31, for the expert's (b) (the research of 2026-10-31 on NASA's metadata): NASA's vocabularies keep a radio band inside an instrument's name and have no kind of thing of its own for a band. GCMD's Instruments list has "L-SAR | L-band Synthetic Aperture Radar", "PALSAR | Phased Array type L-band Synthetic Aperture Radar", "SMAP L-BAND RADAR" and "MIRAS | 2-D Passive L-Band Microwave Interferometer" (11 entries with "L-band"), and no GCMD science keyword or platform has "L-band"; UMM-C puts wavelength among an instrument's free characteristics ("Instrument-specific characteristics, e.g., Wavelength, SwathWidth, Field of View"). That supports option 1, "Aquarius L-band radiometer" whole, as now.

### Quoted for us

- entity class Instrument: a device that takes measurements
- entity class TemporalResolution: an amount of time between one value of the data and the next, e.g. daily; weekly (8 day)
- predicate COMPUTED_FROM: was made by processing this input
- predicate UNIQUE_TO_INSTRUMENT: is found only on this Instrument
- predicate ACQUIRED_BY_INSTRUMENT: was collected by this Instrument
- entity class Wavelength -> Channel: A wavelength band or spectral range, such as an infrared filter band, in which observations are made.
- entity class Frequency -> TemporalResolution: A rate of occurrence, such as daily or weekly, or a radio frequency band, such as S-, X-, or Ku-band.
- Writing a classed triple, rule 14: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.
- Writing a classed triple, rule 19: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 19: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true.

### Consequences

#### Option 1: Keep Channel narrow, and radio bands inside the Instrument's words

- Nothing changes in the ground truth triples above.
- A filter band or a radio band the model extracts as Wavelength is compared as a Channel; one it extracts as Frequency is compared as a TemporalResolution, which no ground truth triple will give it, so it is counted wrong even when the model found the band.

#### Option 2: Widen Channel to any band of the spectrum

- The ground truth schema's definition of Channel, rule 19 of *Writing a classed triple*, and the model's copy of the rules change; the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" gets a triple for "L-band".
- The learning step's instructions change, and its next run costs model calls.

#### Option 3: An entity class of its own for radio bands

- Radio bands and wavelength channels are kept apart, as the answer to (b) may say they should be.
- The rows that hold radio bands are pointed at the new entity class and checked again.

### Affects

- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- classed triple of the record at pool position 4: "skin SST" (Variable) COMPUTED_FROM "long wave IR 11 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "skin SST" (Variable) COMPUTED_FROM "long wave IR 12 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 3.95 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "SST4" (Variable) COMPUTED_FROM "mid-infrared 4.05 micron wavelength channel" (Channel)
- classed triple of the record at pool position 4: "mid-infrared 3.95 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 4: "mid-infrared 4.05 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) ACQUIRED_BY_INSTRUMENT "Aquarius L-band radiometer" (Instrument)
- classed triple of the record at pool position 7: "band 31 emissivity" (Variable) FOR_CHANNEL "band 31" (Channel)
- classed triple of the record at pool position 7: "band 32 emissivity" (Variable) FOR_CHANNEL "band 32" (Channel)
- classed triple of the record at pool position 18: "BRDF geometric parameter for VIIRS band M4 (0.555 μm)" (Variable) FOR_CHANNEL "VIIRS band M4 (0.555 μm)" (Channel)
- translation table row: entity class Wavelength
- translation table row: entity class Frequency
- ground truth schema entry: entity class Channel
- rule: Writing a classed triple, rule 19
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules (the list of qualifiers taken out, rule 19 of *Writing a classed triple*)

## Q14: Is every process or effect a phenomenon, including ones caused by people or by spaceflight?

- status: open
- priority: low
- question kind: translation table rows
- in short: the translation table's row for PhysicalPhenomenon (current or past schema), into the ground truth schema's Phenomenon

### The question

Our schema has an entity class Phenomenon, "something that happens in nature and can be observed", such as the sun glint in the example below. The [model](../docs/terminology.md#8-the-pipeline) we test learned its own schema from other records, and its nearest entity class, PhysicalPhenomenon, also takes in effects caused by people or by spaceflight, such as "biological responses to spaceflight" (both definitions below). When we score the model, we count its PhysicalPhenomenon as our Phenomenon. We would like to know:

- (a) Is an effect caused by people or by spaceflight a phenomenon in the same sense as a natural one? If not, should our Phenomenon be widened ("something that happens, in nature or caused by people, and can be observed"), or should such effects be something else? For instance, one record says its data products were "discontinued on November 16, 2022, due to significant loss of data retrieval following the Constellation Exit Maneuvers"; we wrote that loss as an Issue, "a problem that affects how data are made or used", not as a Phenomenon.

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: The SST4 product has lower uncertainty, but due to sun glint can only be used at night
- classed triple: "SST4" (Variable) LIMITED_BY "sun glint" (Phenomenon)

### Ground truth schema

- entity class Phenomenon: something that happens in nature and can be observed, e.g. sun glint
- entity class Issue: a problem that affects how data are made or used, e.g. loss of data retrieval

### Translation table

- entity class PhysicalPhenomenon -> Phenomenon: A natural or induced process, event, or effect, such as radiation-belt electron losses, signal refraction, or biological responses to spaceflight, that is observed or studied.

### Options

#### Option 1: Keep counting PhysicalPhenomenon as Phenomenon

The model's PhysicalPhenomenon keeps counting as our Phenomenon.

#### Option 2: Widen Phenomenon's definition

Our Phenomenon also holds effects caused by people or by spaceflight.

#### Option 3: Keep natural and induced effects apart

The model's PhysicalPhenomenon no longer counts as our Phenomenon: it counts as nothing in our schema, or as an entity class of its own for induced effects.

### My current reading

Option 1 for now: the only phenomenon in the records we have read so far, sun glint, fits both definitions. Your answer decides between option 2 and option 3.

### My notes

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", the only tuning record annotated so far with a Phenomenon; since "sun glint" fits both definitions, the row translates it rightly, which is why this question's priority is low. A classed triple that uses a row naming (none) can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only. Option 3's entity class would be one we coin once a tuning record needs one.

The record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" has the induced effect named in the context, written as an Issue (coined 2026-10-25, for us to confirm; supported on 2026-10-31 by the SWEET ontology, below); its two classed triples with it are listed under Affects. Changed on 2026-10-31: the Issue is now "loss of data retrieval following the Constellation Exit Maneuvers", without "significant" (rule 5 of *What counts as a fact*: opinion words are left out), in both classed triples; the ground truth schema's Issue now gives "loss of data retrieval" as its example.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The old (a) and (b) are now the expert's (a); the options were "Keep the row" (now "Keep counting PhysicalPhenomenon as Phenomenon") and "Translate PhysicalPhenomenon into (none), or into an entity class of its own" (now "Keep natural and induced effects apart"), same meaning.

- The question, as it was: The ground truth schema's Phenomenon is "something that happens in nature and can be observed, e.g. sun glint". The schema the model learned has an entity class PhysicalPhenomenon, "A natural or induced process, event, or effect, such as radiation-belt electron losses, signal refraction, or biological responses to spaceflight, that is observed or studied", which the translation table translates into Phenomenon.
- (a) Is every natural or induced process or effect, as PhysicalPhenomenon has it, a Phenomenon in the sense of the ground truth schema, including effects caused by people or by spaceflight (biological responses to spaceflight)?
- (b) If not: should Phenomenon's definition be widened ("something that happens, in nature or caused by people, and can be observed"), or should induced effects be something else?

The question's context, as it was: The records we have read so far have one Phenomenon, "sun glint", in the example below. It fits both definitions; the question is about records still to come.

The record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" has an effect caused by spaceflight: "Production of V6 Terra MODIS Land Surface Temperature and Emissivity (LST&E) data products was discontinued on November 16, 2022, due to significant loss of data retrieval following the Constellation Exit Maneuvers". Since Phenomenon is "something that happens in nature", we wrote it as an Issue, an entity class we coined: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) PRODUCTION_DISCONTINUED_DUE_TO "significant loss of data retrieval following the Constellation Exit Maneuvers" (Issue). If Phenomenon is widened (option 2), it may become a Phenomenon instead.

How the translation table is used: the model extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with ours, each entity class and predicate of that schema is replaced by the one of the ground truth schema its row of the translation table names. A row that names (none) says nothing in the ground truth schema means the same.

Checked on 2026-10-31: the SWEET ontology files human-caused effects on the environment under phenomena (sophei:EnvironmentalImpact is a subclass of soph:Phenomena, and sophei:Pollution of EnvironmentalImpact), and keeps human activities apart (sohu:HumanActivity) (https://github.com/ESIPFed/sweet, src/phenEnvirImpact.ttl and src/human.ttl). So the current schema's PhysicalPhenomenon, which takes in induced effects, has precedent, and a data loss after a spacecraft's maneuver as an Issue, not a Phenomenon, is supported; if option 2 is chosen, SWEET's split gives its wording ("something that happens in nature, including effects of human activity on the environment, and can be observed"). The count of induced effects in step 040's evidence, on the NASA laptop, is still to make.

### Quoted for us

- predicate LIMITED_BY: its use is restricted by
- predicate PRODUCTION_DISCONTINUED_DUE_TO: stopped being produced because of
- Writing a classed triple, rule 14: Entity classes and predicates: the ground truth schema's, when one fits, so records name the same things the same way.

### Consequences

#### Option 1: Keep counting PhysicalPhenomenon as Phenomenon

- Right for "sun glint", and for any natural process.
- An induced effect the model extracts is compared as a Phenomenon, which the ground truth schema's definition ("happens in nature") doesn't cover: counted right, or wrong, depending on how the annotator read the definition.
- Nothing changes now.

#### Option 2: Widen Phenomenon's definition

- The ground truth schema's definition changes, and the row into it is checked again.
- The ground truth written so far stays right, since "sun glint" fits both.

#### Option 3: Keep natural and induced effects apart

- The row translates PhysicalPhenomenon into (none), or into an entity class of its own: classed triples that use PhysicalPhenomenon count as extracted only (with (none)), natural ones too, until the ground truth schema has an entity class for them.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "SST4" (Variable) LIMITED_BY "sun glint" (Phenomenon)
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) PRODUCTION_DISCONTINUED_DUE_TO "loss of data retrieval following the Constellation Exit Maneuvers" (Issue)
- classed triple of the record at pool position 7: "loss of data retrieval following the Constellation Exit Maneuvers" (Issue) DOCUMENTED_AT "https://landweb.modaps.eosdis.nasa.gov/displayissue?id=98" (WebPage)
- translation table row: entity class PhysicalPhenomenon
- ground truth schema entry: entity class Phenomenon

## Q15: Is a coordinate system a map projection?

- status: open
- priority: low
- question kind: translation table rows
- in short: the translation table's rows for CoordinateSystem and HAS_COORDINATE_SYSTEM (current or past schema), and the ground truth schema's MapProjection

### The question

Our schema has an entity class MapProjection, "a way of drawing the curved Earth on a flat map", such as the "equidistant cylindrical" projection in the example below. The [model](../docs/terminology.md#8-the-pipeline) we test learned its own schema from other records, and its nearest entity class is CoordinateSystem, "a spatial reference frame or grid, such as a heliographic system or equidistant grid" (both definitions below). When we score the model, we count its CoordinateSystem as our MapProjection. We would like to know: is every coordinate system that records of this catalog name a map projection? Our reading is that it isn't: a coordinate system says how a position is given (a heliographic system gives positions on the Sun), a map projection says how a curved surface is drawn flat, and a grid, a fixed set of cells that values are collected into, is a third thing. If so, where should a coordinate system go?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical
- source text: an equidistant cylindrical (also known as Platte Carre projection
- classed triple: "pixels" (Dataset) MAPPED_INTO "equidistant cylindrical" (MapProjection)
- classed triple: "equidistant cylindrical" (MapProjection) ALSO_KNOWN_AS "Platte Carre" (MapProjection)

### Ground truth schema

- entity class MapProjection: a way of drawing the curved Earth on a flat map, e.g. equidistant cylindrical
- entity class Grid: a fixed set of cells or points that data values are given on, e.g. ISEAG; pressure grid with 24 levels per decade

### Translation table

- entity class CoordinateSystem -> MapProjection: A spatial reference frame or grid, such as a heliographic system or equidistant grid, used to locate or map data.

### Options

#### Option 1: Keep counting a coordinate system as a map projection

The model's CoordinateSystem keeps counting as our MapProjection.

#### Option 2: Keep coordinate systems apart from map projections

The model's CoordinateSystem no longer counts as our MapProjection: it counts as nothing in our schema, or as an entity class of its own for coordinate systems that aren't map projections.

### My current reading

Option 1: in the records we have read so far, the only coordinate system is a map projection. We would choose option 2 if other coordinate systems are common in the catalog.

### My notes

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", the only tuning record whose ground truth so far has a map projection as an object instance, so the rows translate it rightly; that is why this question's priority is low: one record, and the facts are written down either way. A classed triple that uses a row naming (none) can never be part of a [pair](../docs/terminology.md#7-evaluating-extraction-step-070) with a ground truth triple, so it always counts as extracted only. Option 2's entity class (and predicate) would be ones we coin in the ground truth schema once a tuning record names a coordinate system that isn't a map projection.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The old (b) and (c) are now the expert's (b). The options were "Keep the rows and the record's spelling" (now "Keep counting a coordinate system as a map projection, and the record's spelling") and "Translate CoordinateSystem into (none), or into an entity class of its own" (now "Keep coordinate systems apart from map projections"), same meaning. The example also showed the source text "Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/" and the classed triple "equidistant cylindrical" (MapProjection) DOCUMENTED_AT "https://oceancolor.gsfc.nasa.gov/docs/format/" (WebPage), still under Affects.

- The question, as it was: The schema the model learned has an entity class CoordinateSystem: "A spatial reference frame or grid, such as a heliographic system or equidistant grid, used to locate or map data", and a predicate HAS_COORDINATE_SYSTEM. The translation table translates them into the ground truth schema's MapProjection, "a way of drawing the curved Earth on a flat map, e.g. equidistant cylindrical", and MAPPED_INTO.
- (a) Is every coordinate system a record of this catalog names a map projection? Our reading is that it isn't: a coordinate system says how a position is given (e.g. a heliographic system, positions on the Sun), while a map projection says how a curved surface is drawn flat; and a grid ("a fixed set of cells that data values are collected into, e.g. ISEAG") is a third thing. If so, where should a coordinate system go?
- (b) The record below writes "Platte Carre". Is that the projection usually spelled "Plate Carrée", and is it the same projection as "equidistant cylindrical", so that the fact "equidistant cylindrical" (MapProjection) ALSO_KNOWN_AS "Platte Carre" (MapProjection) is true?
- (c) Should the knowledge graph keep a record's own spelling ("Platte Carre"), as the annotation guidelines do now, or the usual one?

The question's context, as it was: How the translation table is used: the model extracts classed triples with a schema it learned from other records of the catalog (the current schema; a schema an earlier run used is a past schema). Before its classed triples are compared with ours, each entity class and predicate of that schema is replaced by the one of the ground truth schema its row of the translation table names. A row that names (none) says nothing in the ground truth schema means the same.

The record below is the only one so far where we wrote down a map projection. We kept the record's own words, as rule 11 of *Writing a classed triple* says, also for "Platte Carre".

Taken out of the expert's view on 2026-10-26, as a question we can settle from sources; kept here word for word. The title was "Is a coordinate system a map projection, and how should "Platte Carre" be written?"; the expert's (a) is now the question, without its letter. Option 1 was "Keep counting a coordinate system as a map projection, and the record's spelling", and its text ended "; we keep "Platte Carre" as the record writes it.". My current reading said "the only coordinate system is a map projection, and we keep the record's own spelling", and ended "common in the catalog (a).". Option 2's consequences said "(question (a))".

- (b) The example writes "equidistant cylindrical (also known as Platte Carre projection". Is "Platte Carre" the projection usually spelled "Plate Carrée", and is it the same projection as "equidistant cylindrical"? We keep a record's own spelling: would that mislead someone searching for it?

Checked on 2026-10-26: Esri's page on the projection (https://desktop.arcgis.com/en/arcmap/latest/map/projections/plate-carree.htm) says "The plate carrée map projection is an equidistant cylindrical projection with the standard parallel located at the equator", and PROJ, the map projection library, names it "Equidistant Cylindrical (Plate Carrée)" (https://proj4.org/operations/projections/eqc.html). PO.DAAC's page for this dataset (https://podaac.jpl.nasa.gov/dataset/MODIS_AQUA_L3_SST_MID-IR_8DAY_4KM_NIGHTTIME_V2019.0) gives "Projection Type: Cylindrical Lat-Lon", a grid of equal steps in latitude and longitude, which is the plate carrée case (our reading of "Cylindrical Lat-Lon"). So "Platte Carre" is the record's misspelling of "Plate Carrée", and the fact "equidistant cylindrical" (MapProjection) ALSO_KNOWN_AS "Platte Carre" (MapProjection) is true for this record: checked. Whether the knowledge graph should also hold the usual spelling, for searches, is ours to decide, not a question for a source; rule 11 of *Writing a classed triple* keeps the record's own words, so the ground truth stays as it is.

Checked on 2026-10-31: the standard agrees with our reading. OGC's Abstract Specification Topic 2 (ISO 19111): "coordinate system: set of mathematical rules for specifying how coordinates are to be assigned to points"; "map projection: coordinate conversion from an ellipsoidal coordinate system to a plane"; a projected coordinate reference system is one "derived from a geographic coordinate reference system by applying a map projection" (OGC 18-005r5, section 3, https://docs.ogc.org/as/18-005r5/18-005r5.html). So a latitude-longitude or heliographic system is a coordinate system with no projection, and counting the current schema's CoordinateSystem as our MapProjection is wrong for any such instance; if option 2 is chosen, ISO's "coordinate reference system" is the standard name for the new entity class. What is left is a count, of the coordinate systems in step 040's evidence that are not projections (on the NASA laptop).

### Quoted for us

- predicate MAPPED_INTO: its values were laid onto a map drawn with this MapProjection
- predicate ALSO_KNOWN_AS: is the same thing under another name
- predicate DOCUMENTED_AT: more details about it are written at this WebPage or in this Document
- predicate HAS_COORDINATE_SYSTEM -> MAPPED_INTO: The subject (a dataset) is expressed in, projected to, or mapped onto the object, a coordinate system or grid projection.
- Writing a classed triple, rule 11: Subject instance and object instance: the record's own words, as written. Don't paraphrase them, and don't expand an abbreviation the record leaves unexpanded.
- Writing a classed triple, rule 23: One thing, one wording, within a record.
- Writing a classed triple, rule 23: the others appear only in an ALSO_KNOWN_AS triple, and only if the record states one (rule 20).

### Consequences

#### Option 1: Keep counting a coordinate system as a map projection

- The rows for CoordinateSystem and HAS_COORDINATE_SYSTEM stay, translating into MapProjection and MAPPED_INTO.
- Right when a coordinate system the model extracts is a map projection; counted wrong when it is a coordinate system of another sort (a heliographic system).
- The knowledge graph holds the record's spelling, so a search for "Plate Carrée" misses it.
- Nothing changes now.

#### Option 2: Keep coordinate systems apart from map projections

- CoordinateSystem and HAS_COORDINATE_SYSTEM translate into (none), or into an entity class (and a predicate) of their own.
- Map projections the model files under CoordinateSystem then count as extracted only (with (none)), or are compared with a coordinate system entity class the ground truth doesn't use for them.
- Right only if coordinate systems that aren't map projections are common in the catalog (the question).

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "pixels" (Dataset) MAPPED_INTO "equidistant cylindrical" (MapProjection)
- classed triple of the record at pool position 4: "equidistant cylindrical" (MapProjection) ALSO_KNOWN_AS "Platte Carre" (MapProjection)
- classed triple of the record at pool position 4: "equidistant cylindrical" (MapProjection) DOCUMENTED_AT "https://oceancolor.gsfc.nasa.gov/docs/format/" (WebPage)
- translation table row: entity class CoordinateSystem
- translation table row: predicate HAS_COORDINATE_SYSTEM
- ground truth schema entry: entity class MapProjection
- ground truth schema entry: predicate MAPPED_INTO
- rule: Writing a classed triple, rule 11
- rule: Writing a classed triple, rule 23

## Q16: Is the time "13:30" in Aqua's orbit a fact of its own?

- status: withdrawn
- priority: low
- question kind: schema entry
- in short: the ground truth schema's Orbit and TimeOfDay, and rule 19 of *Writing a classed triple* in the annotation guidelines

### The question

The example below says that Aqua was launched "into a sun synchronous, polar orbit with a daylight ascending node at 13:30". We keep that whole passage as one orbit: Aqua HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30". Our schema's only predicate for a time of day says "comes from observations made at" that time, which doesn't fit an orbit, so "13:30" can't be a [fact](../docs/terminology.md#2-triples) of its own without a new predicate. We would like to know:

- (a) Is the time of the ascending node (13:30) something people who use this catalog search on by itself, for instance to find the satellites that cross the equator in the early afternoon? Our reading, not checked against a source: the ascending node is where the orbit crosses the equator going north, and 13:30 is the local time at which it does so in daylight.
- (b) Are "sun synchronous" and "polar" two properties of the orbit, each worth a fact of its own, or does "sun synchronous, polar orbit" name one type of orbit?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30
- classed triple: "Aqua" (Platform) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)

### Ground truth schema

- entity class Orbit: a path a spacecraft travels around a CelestialBody
- predicate HAS_ORBIT: travels in this Orbit
- entity class TimeOfDay: a point or period in the day, which comes back every day, e.g. 2:39 PM; morning; nighttime
- predicate OBSERVED_AT_TIME_OF_DAY: comes from observations made at or during this TimeOfDay

### Options

#### Option 1: Keep the orbit whole

One fact, as now: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit).

#### Option 2: The time as a ground truth triple of its own

A new predicate, e.g. HAS_ASCENDING_NODE_TIME ("crosses the equator going north at this TimeOfDay"), and two facts: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit" (Orbit), and a second one that gives "13:30" (TimeOfDay).

#### Option 3: Split the orbit into all its properties

As option 2, and "sun synchronous" and "polar" also become facts of their own (question (b)).

### My current reading

Option 1, keep the orbit whole: our rules keep a time inside an instance when taking it out would give a fact that isn't true, and the records we have read so far name an orbit only once (Aqua's, in the example). We would change to option 2 if people search this catalog by the time a satellite crosses the equator.

### My notes

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", the only tuning record annotated so far that names an orbit.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The old (c) we settle ourselves once (a) is answered (option 2's second triple has Aqua or the orbit as its subject instance).

- (c) If the time is a fact of its own, what does it belong to: the orbit, or the satellite (Aqua)?

The question's context, as it was: The ground truth schema has a TimeOfDay entity class, and rule 19 of *Writing a classed triple* in the annotation guidelines takes a time of day out of an instance, as a ground truth triple of its own, unless taking it out would give a triple that isn't true. Taking "13:30" out with the only predicate the ground truth schema has for a time of day, OBSERVED_AT_TIME_OF_DAY, would say that the orbit comes from observations made at 13:30, which isn't true. So, by rule 19 of *Writing a classed triple*, "13:30" stays in the orbit's instance. The question is whether the ground truth schema should have another predicate for this time, so that it can be a ground truth triple of its own.

Option 2's text, as it was: A new predicate in the ground truth schema, e.g. HAS_ASCENDING_NODE_TIME ("crosses the equator going north at this TimeOfDay"), and the ground truth writes two classed triples: "Aqua" (Spacecraft) HAS_ORBIT "sun synchronous, polar orbit" (Orbit), and a second one that gives "13:30" (TimeOfDay), with Aqua or the orbit as its subject instance (question (c)).

Withdrawn on 2026-10-26: what it asks of facts we can check in sources, and the rest is ours to decide, so it is no longer asked of the experts; kept whole, so that comments filed under its number still find it.

Checked on 2026-10-26: NASA's page on Aqua (https://science.nasa.gov/mission/aqua/about-aqua-spacecraft-and-instruments/) gives its orbit as "Sun synchronous, near polar orbit" and its "Equatorial crossing" as "1:30 p.m. ascending node": 13:30 is the local time at which Aqua crosses the equator going north, as our reading in (a) said. NASA's Catalog of Earth Satellite Orbits (https://science.nasa.gov/earth/earth-observatory/catalog-of-earth-satellite-orbits) defines the two words apart: a polar orbit "moves around the Earth from pole to pole"; in a sun-synchronous one, "whenever and wherever the satellite crosses the equator, the local solar time on the ground is always the same". So, for (b), "sun synchronous" and "polar" are two properties of the orbit, not the name of one type: checked. Whether people search this catalog by the time a satellite crosses the equator, the rest of (a), no source settles: not settled, our reading: we keep option 1, the orbit whole, as My current reading says; the ground truth stays as it is.

Checked on 2026-10-31, the rest of (a): NASA's own search uses the equator crossing for granules only, not for collections (datasets): its CMR search API has "Find granules by orbit equator crossing longitude" and "Find granules by orbit equator crossing date", and no such parameter for collections (https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html). It stays withdrawn, and the orbit stays whole.

### Quoted for us

- Writing a classed triple, rule 15: One fact per ground truth triple. A sentence that states two facts gives two ground truth triples.
- Writing a classed triple, rule 19: A qualifier that is a temporal resolution, an area the data cover, a processing level, a spatial resolution, a country, a time of day, or a target body is a ground truth triple of its own, and is taken out of the instance.
- Writing a classed triple, rule 19: A qualifier stays in the instance, as written, if it is any other kind ("sea surface salinity" stays whole), or if taking it out would give a triple that isn't true. Suppose: a record says "an afternoon orbit". Then: taking "afternoon" out would give "orbit" OBSERVED_AT_TIME_OF_DAY "afternoon", which says the orbit comes from observations made in the afternoon. That isn't true, so the instance stays "afternoon orbit".

### Consequences

#### Option 1: Keep the orbit whole

- Nothing changes: not the annotation guidelines, not the ground truth schema, not the ground truth.
- The time 13:30 can be found only by searching inside the words of the orbit's instance; a search for satellites by the time they cross the equator has to read those words.
- Two records that describe the same orbit in different words give two different object instances.

#### Option 2: The time as a ground truth triple of its own

- A new predicate in the ground truth schema, and an example for it in the annotation guidelines, so that we write it the same way in every record; the [model](../docs/terminology.md#8-the-pipeline) follows the same rules, so its copy of the rules changes too.
- The orbit's instance loses the words "with a daylight ascending node at 13:30", which are no longer in that triple.
- The time can be searched for by itself.

#### Option 3: Split the orbit into all its properties

- Everything option 2 brings, and more predicates or entity classes for the properties of an orbit.
- More ground truth triples per record that describes an orbit, each of which the model must also extract.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)
- ground truth schema entry: entity class Orbit
- ground truth schema entry: predicate HAS_ORBIT
- rule: Writing a classed triple, rule 15
- rule: Writing a classed triple, rule 19
- pipeline method: annotations/ground_truth_schema.txt: a new predicate for the time an orbit crosses the equator (option 2), or for each property of an orbit (option 3)
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

## Q17: The GRaND residual map is "related to the average atomic mass on Vesta": is there a more specific relationship?

- status: answered
- priority: low
- question kind: records and triples
- in short: the ground truth schema's RELATED_TO and ESTIMATES, and rule 1 of *What counts as a fact* in the annotation guidelines

### The question

A record of data from the GRaND instrument of the Dawn spacecraft says: "The residual map is related to the average atomic mass on Vesta." The ground truth writes this as the dataset RELATED_TO "average atomic mass". We would like to know:

- (a) What is the relationship between the residual map and the average atomic mass: does the residual map give approximate values of the average atomic mass, or is it only one clue among several?
- (b) Would someone in your field read "is related to" in such a record as "gives approximate values for", or only as "has something to do with"?

### Context

We write only what a record states (rule 1 of *What counts as a fact*, quoted below), so a more specific predicate than RELATED_TO needs words in the record that say so. The ground truth schema has ESTIMATES, "gives approximate values for", which the ground truth uses for what a Variable gives approximate values of.

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
- entity class PhysicalQuantity: a bare property that can be measured, whatever method measures it, e.g. temperature; gravity; sea surface temperature; snow cover; not a form the data take, such as images, image cubes, spectra or maps (a SpatialRepresentation)

### Annotation guidelines

- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or abbreviation stands for.

### Options

#### Option 1: Keep RELATED_TO

The ground truth stays as it is: the dataset RELATED_TO "average atomic mass".

#### Option 2: A more specific predicate for the average atomic mass

Only if "related to" here means "gives approximate values for" (question (a)): the dataset ESTIMATES "average atomic mass" in place of RELATED_TO.

### My current reading

Option 1, because "related to" is all the record states. We would change to option 2 if experts say that, in such a record, "related to" means that the map gives approximate values of the average atomic mass.

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

## Q18: SST4: is it a skin sea surface temperature, and lower uncertainty than what?

- status: open
- priority: low
- question kind: records and triples
- in short: the ground truth schema's Variable, ESTIMATES and HAS_LOWER_UNCERTAINTY_THAN, and rule 23 of the annotation guidelines

### The question

The example below, a MODIS sea surface temperature (SST) product, says "Two SST products can be present in these files": "a skin SST produced for both day and night (NSST)", and, at night, "a second SST product", "identified as SST4". From it we wrote that the skin SST gives approximate values of the "skin sea surface temperature (SST)", that SST4 gives approximate values of "SST", and that SST4 has lower uncertainty than the skin SST. We would like to know:

- (b) The record says "The SST4 product has lower uncertainty", without saying than what. We read it as "lower uncertainty than NSST", the other product the record describes. Is that how you read it?
- (e) The record says "The first is a skin SST". We read it as a fact: the first product gives approximate values of the skin sea surface temperature. Or does it only say what kind of product the first one is, which we would write as no fact of its own?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST
- source text: the SST derived from these measurements is identified as SST4
- source text: The SST4 product has lower uncertainty
- source text: Two SST products can be present in these files. The first is a skin SST
- source text: identified as SST4. The SST4 product has lower uncertainty
- classed triple: "skin SST" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)
- classed triple: "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST" (Variable)

### Ground truth schema

- entity class Variable: a property narrowed by a method, a band, a threshold, another object or another constraint, e.g. SST4; NDSI; band 31 emissivity; dust fluences at each of twelve mass thresholds
- entity class PhysicalQuantity: a bare property that can be measured, whatever method measures it, e.g. temperature; gravity; sea surface temperature; snow cover; not a form the data take, such as images, image cubes, spectra or maps (a SpatialRepresentation)
- predicate ESTIMATES: gives approximate values for
- predicate HAS_LOWER_UNCERTAINTY_THAN: its values are more certain than those of

### Options

#### Option 1: Keep the ground truth as it is

The facts stay as written: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity); "skin SST" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity); and "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST" (Variable).

#### Option 2: Leave out the comparison

If "lower uncertainty" doesn't clearly mean "than NSST": no comparison is written, so there is no fact "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST" (Variable).

### My current reading

Option 1, because the comparison with NSST is the only reading we see, with two products introduced as "the first" and "a second".

### My notes

Checked against sources on 2026-10-30: NSST is NASA's nighttime long-wave (11 µm) SST product, "Aqua MODIS Level-3 Global Mapped 11µm Nighttime Sea Surface Temperature (NSST) Data, version R2019.0" (https://data.nasa.gov/dataset/aqua-modis-level-3-global-mapped-11m-nighttime-sea-surface-temperature-nsst-data-version-r); SST4 is a skin SST ("This algorithm returns the skin sea surface temperature", OBPG SST4 ATBD, https://oceandata.sci.gsfc.nasa.gov/files/atbd/legacy/atbd-obdaac-short-wave-sea-surface-temperature.pdf); a MID-IR Nighttime dataset holds sst4 and qual_sst4 only (PO.DAAC, https://podaac.jpl.nasa.gov/dataset/MODIS_AQUA_L3_SST_MID-IR_8DAY_4KM_NIGHTTIME_V2019.0); the sources compare SST4's uncertainty with the long-wave 11/12 µm SST, never "than NSST" in those words.

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0". Until an expert answers, its ground truth keeps option 1, and HAS_VARIABLE "SST4" only. If experts say a "Nighttime" "SST MID-IR" product holds NSST too, we would still write it only if the record says so, and note the gap.

Added on 2026-10-30, (d): the ground truth wrote the product as "skin SST (NSST)" until audit finding G7 (decided on 2026-10-30, docs/improvements.md): "(NSST)" follows "night", so it is not a name with its abbreviation in parentheses (rule 20 of *Writing a classed triple*), and the record does not say what NSST names (rule 1 of *What counts as a fact*). Its seven ground truth triples now use "skin SST", and "NSST" is in annotations/left_out.md. If the answer is that NSST names the skin SST product, the triples would use "skin SST" with "NSST" as another wording (ALSO_KNOWN_AS needs words of the record's own, rule 20, so probably no such triple); if it names the night observations, nothing changes.

Added on 2026-10-31, (e), from the third audit (finding G-3, docs/improvements.md): the source text of "skin SST" ESTIMATES "skin sea surface temperature (SST)" was "The first is a skin SST produced for both day and night (NSST)", which has no words for the object; it now runs from the record's "skin sea surface temperature (SST) products" to "The first is a skin SST" (rule 17 of *Writing a classed triple*: words for the subject, the predicate and the object). Whether "The first is a skin SST" states a fact or only says what kind of product it is (rule 4 of *What counts as a fact*: "Not "is a" facts.") is what (e) asks.

Changed on 2026-10-26, because the review page now shows a record's title only once, in its example: the expert's (c) began "The title is "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0". From its "SST MID-IR" we wrote".

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The sub-questions keep their letters; only the rule numbers and quotes of rules were taken out of them.

- The question, as it was: A record of MODIS sea surface temperature (SST) products describes two SST products in its files: a skin SST made for day and night (NSST), and, at night, a second SST product, identified as SST4. The ground truth now says that NSST gives approximate values of the "skin sea surface temperature (SST)", that SST4 gives approximate values of "SST", and that SST4 has lower uncertainty than NSST.
- (a) Is SST4 a skin SST too, so that both products estimate the same quantity, the skin sea surface temperature? If so, rule 23 of the annotation guidelines (one thing, one wording, within a record) would write "skin sea surface temperature (SST)" for both.
- (b) The record says "The SST4 product has lower uncertainty", without saying than what. The ground truth reads it as "lower uncertainty than NSST", the other product the record describes. Is that how an expert reads it?
- (c) The dataset's title is "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", and the record says "Two SST products can be present in these files". The ground truth says the dataset HAS_VARIABLE "SST4", from the title's "SST MID-IR" (SST4 is the one made from the mid-infrared channels), and writes no HAS_VARIABLE for NSST, since "can be present" is not a statement that it is (rule 7 of *What counts as a fact*: "Not uncertain facts."). Does a "SST MID-IR ... Nighttime" product hold SST4 only, or NSST too?

The question's context, as it was: The record introduces the two products as "Two SST products can be present in these files. The first is a skin SST ... At night, a second SST product ...". Whether "a second SST product" is a skin SST too is what (a) asks: we may use what the words mean to see that two wordings name the same thing (rule 23), but we may not add a fact the record doesn't state (rule 1 of *What counts as a fact*).

Option 2's text, as it was: If SST4 is a skin SST: "SST4" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity), one wording for both, by rule 23.

Taken out of the expert's view on 2026-10-31, as questions we can settle from sources; kept here word for word. The title was "SST4 and NSST: is SST4 a skin sea surface temperature, lower uncertainty than what, and does this product hold both?". My current reading ended: "For (c), we write only that the dataset holds SST4, since "can be present" doesn't state that NSST is there."

- (c) From "SST MID-IR" in the example's title we wrote that the dataset holds SST4 (the product made from the mid-infrared channels), and wrote nothing about NSST, since "can be present" doesn't say that it is there. Does a "SST MID-IR ... Nighttime" product hold SST4 only, or NSST too?
- (d) The record says "a skin SST produced for both day and night (NSST) observations". Does "NSST" name the skin SST product, or something else, such as the observations made at night? We write the product as "skin SST" and leave "NSST" out, since "(NSST)" follows "night", not "skin SST".

Settled from sources (checked on 2026-10-30). (c): a "SST MID-IR ... Nighttime" dataset holds SST4 only. PO.DAAC's page for this dataset (https://podaac.jpl.nasa.gov/dataset/MODIS_AQUA_L3_SST_MID-IR_8DAY_4KM_NIGHTTIME_V2019.0) lists its variables as sst4 and qual_sst4 (with lat, lon and palette), while the Thermal IR dataset of the same family (https://podaac.jpl.nasa.gov/dataset/MODIS_AQUA_L3_SST_THERMAL_8DAY_4KM_NIGHTTIME_V2019.0) holds sst and qual_sst; both carry the same description, "Two SST products can be present in these files". So the ground truth's HAS_VARIABLE "SST4" only is right. (d): "NSST" is the Ocean Biology Processing Group's name for its nighttime long-wave (11 and 12 micron) SST product: "Aqua MODIS Level-3 Global Mapped 11µm Nighttime Sea Surface Temperature (NSST) Data, version R2019.0" (https://data.nasa.gov/dataset/aqua-modis-level-3-global-mapped-11m-nighttime-sea-surface-temperature-nsst-data-version-r), and the long-wave algorithm document speaks of "the 11-12 μm night NSST product" (https://oceandata.sci.gsfc.nasa.gov/files/atbd/legacy/atbd-obdaac-long-wave-sea-surface-temperature.pdf). It names neither the record's day-and-night "skin SST" nor the night observations, so it stays left out (rule 1 of *What counts as a fact*: the record doesn't explain it), as annotations/left_out.md says; nothing changes.

Taken out of the expert's view on 2026-10-31, as settled from a source (the research of 2026-10-31); kept here word for word: "- (a) Is SST4 a skin SST too, so that both products estimate the same quantity, the skin sea surface temperature? We would then write the same words for both." Option 2, "Both estimate the skin sea surface temperature", was: "If SST4 is a skin SST: "SST4" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity), the same words for both." Its consequences: "One ground truth triple changes its object instance. The record's word for SST4's quantity is "SST", so this relies on rule 23's "what you know about the words", which an expert has to confirm." Option 1's consequences also said: "If SST4 is a skin SST, the two products appear to estimate two different quantities ("SST" and "skin sea surface temperature (SST)"), and a search for skin SST data finds only NSST." Option 3 is now option 2. My current reading, as it was: "Option 1, because the record names SST4's quantity only "SST", and the comparison with NSST is the only reading we see, with two products introduced as "the first" and "a second"."

Settled on 2026-10-31: SST4 is a skin SST, as the OBPG's SST4 document says ("This algorithm returns the skin sea surface temperature in units of °C", above), but the record says only "SST" there, so "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity) stays (rule 1 of *What counts as a fact*; research B9, docs/improvements.md, *Considered and not changed*); the source's fact is for 080's enrichment. No expert answer could change the triple, so (a) is no longer asked. The expert's (b) stays: NASA's OB.DAAC compares SST4 with the long-wave product, "reduced sensitivity to atmospheric water vapor compared with long-wave (11/12 µm) split-window SST" (strong secondary, research M3), and no sentence says "than NSST"; how to read the record's sentence is the expert's. For the expert's (e): in knowledge graph practice "X is a Y" states a type (Wikidata's P31, "instance of"), and the CF conventions name the skin temperature as a quantity of its own, sea_surface_skin_temperature, "the temperature within the conductive diffusion-dominated sub-layer at a depth of approximately 10 - 20 micrometers below the air-sea interface" (the CF standard name table, https://cfconventions.org/Data/cf-standard-names/current/src/cf-standard-name-table.xml); so the type names what the product's values are of, and the current reading, a fact, maps it into our schema, which has no "is a" predicate (my reading).

### Quoted for us

- predicate MORE_ACCURATE_THAN -> HAS_LOWER_UNCERTAINTY_THAN: Links a measurement method or instrument to another method that it outperforms in accuracy.
- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or abbreviation stands for.
- What counts as a fact, rule 7: Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends.
- Writing a classed triple, rule 23: One thing, one wording, within a record. When a record names the same thing more than once, in different words, use the first wording this order picks; the others appear only in an ALSO_KNOWN_AS triple, and only if the record states one (rule 20). 1. The wording that says more: it contains the other's words, each as a whole word, is more precise, or spells out the other's abbreviation.

### Consequences

#### Option 1: Keep the ground truth as it is

- Nothing changes.

#### Option 2: Leave out the comparison

- One ground truth triple fewer; the record's statement that SST4 is more certain is no longer in the ground truth at all, since a comparison needs two sides.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "skin SST" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)
- classed triple of the record at pool position 4: "SST4" (Variable) HAS_LOWER_UNCERTAINTY_THAN "skin SST" (Variable)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VARIABLE "SST4" (Variable)
- rule: What counts as a fact, rule 7
- translation table row: predicate MORE_ACCURATE_THAN
- ground truth schema entry: predicate ESTIMATES
- ground truth schema entry: predicate HAS_LOWER_UNCERTAINTY_THAN
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 23
- rule: What counts as a fact, rule 4

## Q19: Versions: is a MODIS "Collection" a version?

- status: withdrawn
- priority: low
- question kind: records and triples
- in short: the ground truth schema's Version, HAS_VERSION and ALSO_KNOWN_AS, and rule 20 of *Writing a classed triple* in the annotation guidelines

### The question

Records name a dataset's version in several ways. The example says "The terms "Version 61" and "Collection 6.1" are used interchangeably in reference to this release of MODIS data", and we wrote that the dataset has the version "Version 61", also known as "Collection 6.1" (Version and ALSO_KNOWN_AS are defined below). We would like to know:

Is a MODIS "Collection" a version of this one dataset, or a reprocessing of all MODIS products at once, which this dataset is part of (and so something the dataset belongs to, not its version)?

### Example record

- record id: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- pool position: 2
- title: MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061
- notes: This global Level-2 (L2) data set provides daily snow cover detected using Normalized Difference Snow Index (NDSI) and a series of screens designed to alleviate errors and flag uncertain snow cover detections. The NDSI is derived from radiance data acquired by the Moderate Resolution Imaging Spectroradiometer (MODIS) on board the Aqua satellite: DOI:10.5067/MODIS/MYD02HKM.061 and DOI:10.5067/MODIS/MYD021KM.061. Each data granule contains 5 minutes of swath data observed at a resolution of 500 m.

  The terms "Version 61" and "Collection 6.1" are used interchangeably in reference to this release of MODIS data.
- source text: The terms "Version 61" and "Collection 6.1" are used interchangeably in reference to this release of MODIS data
- classed triple: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_VERSION "Version 61" (Version)
- classed triple: "Version 61" (Version) ALSO_KNOWN_AS "Collection 6.1" (Version)

### Ground truth schema

- entity class Version: a label that marks one release of something
- predicate HAS_VERSION: carries this Version
- predicate ALSO_KNOWN_AS: is the same thing under another name

### Options

#### Option 1: Another name of the version (as now)

"Collection 6.1" is another name of the dataset's version: "Version 61" (Version) ALSO_KNOWN_AS "Collection 6.1" (Version).

#### Option 2: Something the dataset belongs to

"Collection 6.1" is a reprocessing of all MODIS products, which the dataset belongs to, written with a kind of thing and a relationship of its own; "Version 61" stays the dataset's version.

### My current reading

Option 1, since the record says the two terms "are used interchangeably". If a Collection is a reprocessing of all MODIS products, "Collection 6.1" would need a kind of thing and a relationship of its own (something the dataset belongs to), which our schema doesn't have yet (option 2).

### My notes

Checked against sources on 2026-10-30: "R2019.0" and "V2019.0" are one release (PO.DAAC's release note, https://podaac.jpl.nasa.gov/highlights/NASA_OBPG_JPL_MODIS_L2P_L3_SST_v2019.0_Datasets_Release); a MODIS "Collection" is "basically a very broad MODIS data version" (MODIS Atmosphere); for MOD11A1, NASA's LP DAAC said it "will cease distribution" of Version 6 and "Users are encouraged to transition to" Version 6.1, never "replace" or "supersede", which is the test now in SUPERSEDES's definition.

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0"; (c) is about the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061". Until an expert answers, the ground truth keeps option 1, and "Version 61" ALSO_KNOWN_AS "Collection 6.1". (d) is about the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (decided 2026-10-25, for us to confirm; confirmed on 2026-10-31, below: "V006", "Version 6" and "V6" are one version): "Version 6", and "Version 6.1" SUPERSEDES "Version 6"; the DOI of Version 6.1 is left out by rule 21 (`annotations/left_out.md`). (e) is about the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0": we first left "first version" out; it is now kept as "V1.0" ALSO_KNOWN_AS "first version", by rule 10 of *What counts as a fact* ("V1.0 stays the first version whatever is released later"). If the answer says otherwise, that ground truth triple is deleted or changed. (The letters in this paragraph are those of the sub-questions as they were, below.)

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The old (a) and (b) are now the expert's (a); the old (c) their (b) (without "is the title's V061 that same Version 61?", which we settle ourselves); the second half of the old (d) their (c). Left for us: whether "V006", "Version 6" and "V6" are one version (the first half of the old (d): the record's own words name one product, so we read them as one), and the old (e), which the annotation guidelines' own example settles ("V1.0" ALSO_KNOWN_AS "first version").

- The question, as it was: A record's title ends in "V2019.0", and its notes say "The R2019.0 supersedes the previous v2014.1 datasets". We read "R2019.0" and "V2019.0" as two names of one release, and wrote: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VERSION "V2019.0" (Version), and "V2019.0" (Version) SUPERSEDES "v2014.1" (Version).
- (a) Are "R2019.0" and "V2019.0" the same release of the data? Our reading, not checked against a source: "R" may stand for a reprocessing, and the reprocessing of 2019 made version 2019.0.
- (b) If they are not the same, what is "R2019.0": a reprocessing, a release of the processing software, or something else?
- (c) The record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says "The terms "Version 61" and "Collection 6.1" are used interchangeably in reference to this release of MODIS data". We wrote the facts "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_VERSION "Version 61" (Version) and "Version 61" (Version) ALSO_KNOWN_AS "Collection 6.1" (Version). Is a MODIS "Collection" a version of this one dataset, or a reprocessing of all MODIS products at once, which this dataset is part of (and so something the dataset belongs to, not its version)? And is the title's "V061" that same Version 61?
- (d) The record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" writes its version three ways: "V006" in its title, "Version 6" twice in its notes, and "V6" once. We read them as one version, and wrote "Version 6", the wording that spells it out (rule 23). Its notes begin "The MOD11A1 Version 6 data product was decommissioned on July 31, 2023. Users are encouraged to use the MOD11A1 Version 6.1 data product.", and we wrote "Version 6.1" (Version) SUPERSEDES "Version 6" (Version), as for "V2019.0" above. Are "V006", "Version 6" and "V6" one version? And does the record say that Version 6.1 replaces Version 6, or only recommend it?
- (e) The record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" says "This version V1.0 is the first version of this dataset". We wrote "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_VERSION "V1.0" (Version). We also wrote "V1.0" (Version) ALSO_KNOWN_AS "first version" (Version), since V1.0 stays the first version whatever is released later (decided 2026-10-25). Is that right, or is "the first version" a fact of another kind (the dataset has no earlier version)?

The question's context, as it was: Rule 23 of the annotation guidelines writes one thing with one wording in a record: of two wordings that say the same, the one the record uses most often, or, on a tie, the one it gives first. Each wording appears once, and the title comes first, so we wrote "V2019.0". If they are two names of one release, rule 20 of *Writing a classed triple* allows an ALSO_KNOWN_AS triple only when the record gives the other name in words of its own, which it doesn't here.

Option 2's text, as it was: They differ: "R2019.0" SUPERSEDES "v2014.1" (Version), as the record writes it, with "R2019.0" in an entity class that fits what it is (question (b)), and the dataset still HAS_VERSION "V2019.0" (Version).

Taken out of the expert's view on 2026-10-31, as questions we can settle from sources; kept here word for word. The expert's question is the old (b), without its letter and with its record as the example; the old (a) and (c) are settled (below). The title was "Versions and releases: are "R2019.0" and "V2019.0" the same release, and is a MODIS "Collection" a version?"; the in-short line was "the ground truth schema's Version, HAS_VERSION, SUPERSEDES and ALSO_KNOWN_AS, and rules 20 and 23 of *Writing a classed triple* in the annotation guidelines". The options were about the old (a); they and my current reading are replaced by ones about the old (b), and the old ones are below. The classed triples of the old example, and those of the old (c), stay under Affects.

- The question's opening, as it was: Records name a dataset's version in several ways, and we are not sure some of them mean what we wrote. The example's title ends in "V2019.0", and its notes say "The R2019.0 supersedes the previous v2014.1 datasets". We read "R2019.0" and "V2019.0" as two names of one release, and wrote that the dataset HAS_VERSION "V2019.0", and that "V2019.0" SUPERSEDES "v2014.1". We would like to know:
- (a) Are "R2019.0" and "V2019.0" the same release of the data? If not, what is "R2019.0": a reprocessing, a release of the processing software, or something else? Our reading, not checked against a source: "R" may stand for a reprocessing, and the reprocessing of 2019 made version 2019.0.
- (b) The record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" says "The terms "Version 61" and "Collection 6.1" are used interchangeably in reference to this release of MODIS data". We wrote that the dataset has the version "Version 61", also known as "Collection 6.1". Is a MODIS "Collection" a version of this one dataset, or a reprocessing of all MODIS products at once, which this dataset is part of (and so something the dataset belongs to, not its version)?
- (c) The record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" begins "The MOD11A1 Version 6 data product was decommissioned on July 31, 2023. Users are encouraged to use the MOD11A1 Version 6.1 data product." We wrote that "Version 6.1" SUPERSEDES "Version 6". Does the record say that Version 6.1 replaces Version 6, or only recommend it?
- The example was the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", with the source texts "V2019.0" and "The R2019.0 supersedes the previous v2014.1 datasets", and the classed triples "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VERSION "V2019.0" (Version) and "V2019.0" (Version) SUPERSEDES "v2014.1" (Version); the ground truth schema part also gave SUPERSEDES (now quoted for us below).
- Option 1, "The same release (as now)", as it was: They are one release, written as now: the dataset HAS_VERSION "V2019.0" (Version), and "V2019.0" (Version) SUPERSEDES "v2014.1" (Version).
- Option 2, "Two different things", as it was: They differ: "R2019.0" SUPERSEDES "v2014.1", as the record writes it, with "R2019.0" written as what your answer to (a) says it is, and the dataset still HAS_VERSION "V2019.0" (Version).
- My current reading, as it was: Option 1, because the record calls both the release that replaces v2014.1, and nothing in it says they differ. We would change to option 2 if "R" and "V" mark different things in NASA's ocean products. For (b), we keep "Version 61" also known as "Collection 6.1", since the record says the two terms "are used interchangeably"; if a Collection is a reprocessing of all MODIS products, "Collection 6.1" would need a kind of thing and a relationship of its own (something the dataset belongs to), which our schema doesn't have yet.
- Option 1's consequences, as they were: Nothing changes. The word "R2019.0" isn't in the ground truth; a search for it won't find this record.
- Option 2's consequences, as they were: "R2019.0" is linked to the dataset by no ground truth triple, since the record doesn't say how the two relate; the annotation tool flags such a triple as not connected to the record's id. Perhaps a new entity class, if "R2019.0" is neither a Version nor anything the ground truth schema has.

Settled from sources, checked on 2026-10-30 (above). The old (a): "R2019.0" and "V2019.0" are one release. PO.DAAC's release note is titled "NASA OBPG/JPL MODIS L2P/L3 SST v2019.0 Datasets Release" and says "The recent R2019.0 processing of the Aqua/Terra Moderate-resolution Imaging Spectroradiometer (MODIS) … has made significant improvements from the previous R2014.0 SST version" (https://podaac.jpl.nasa.gov/highlights/NASA_OBPG_JPL_MODIS_L2P_L3_SST_v2019.0_Datasets_Release); "R" marks the Ocean Biology Processing Group's reprocessings (R2014.0, R2018.0, R2019.0, R2022.0; strong secondary, no page defines the "R" in words). So the old option 1 holds, and the ground truth stays as it is. The old (c): LP DAAC's own words are "will cease distribution" of Version 6.0 and "Users are encouraged to transition to MODIS Version 6.1 (V6.1) data products", never "replace" or "supersede" (https://www.earthdata.nasa.gov/data/alerts-outages/final-notice-modis-version-6-0-land-data-products-decommissioned-july-31-2023); the record's words are the same pattern, and SUPERSEDES's definition settles it: "A record states this when it says the older one is discontinued or decommissioned and directs users to the newer one". So "Version 6.1" SUPERSEDES "Version 6" stays.

Withdrawn on 2026-10-31: settled from sources, so it is no longer asked of the experts; kept whole, so that comments filed under its number still find it. Both readings are true (the sources of 2026-10-30, above): a MODIS Collection is the version label of each product and a reprocessing run shared by all MODIS products; the record says the two terms "are used interchangeably", so "Version 61" (Version) ALSO_KNOWN_AS "Collection 6.1" (Version) stays (option 1). Linking the datasets of one Collection, a shared reprocessing campaign, is a design choice for the graph, not a fact of the ground truth: docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080), and Q24.

Checked on 2026-10-31, the note left for us above on whether "V006", "Version 6" and "V6" are one version: they are. NASA's page for the product writes "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006", "MOD11A1 Version 006" with the one DOI 10.5067/MODIS/MOD11A1.006, "The MOD11A1 Version 6 data product was decommissioned on July 31, 2023" and "Production of V6 Terra MODIS Land Surface Temperature and Emissivity (LST&E) data products was discontinued" (https://www.earthdata.nasa.gov/data/catalog/lpcloud-mod11a1-006). So the ground truth's one "Version 6" stands (rule 23). The "R" of "R2019.0" (above): NASA's pages name the OBPG's reprocessings by these numbers, e.g. "Aqua MODIS Mini-reprocessing R2022.0.3" (https://www.earthdata.nasa.gov/data/alerts-outages/aqua-modis-mini-reprocessing-r2022.0.3); still no page defines the letter in words (strong secondary), and no ground truth triple depends on it.

### Quoted for us

- predicate SUPERSEDES: replaces this earlier one. A record states this when it says the older one is discontinued or decommissioned and directs users to the newer one
- What counts as a fact, rule 10: Not words that are true only as of when the record was written. Leave out "latest", "current", "now", "then available", and words like them. Keep the rest of the fact.
- What counts as a fact, rule 10: Suppose: a record says "V1.0 is the first version." Then: "V1.0" ALSO_KNOWN_AS "first version", because V1.0 stays the first version whatever is released later.
- Writing a classed triple, rule 20: A name with its own abbreviation, another name or code of its own, or a short note in parentheses is one instance, as written. Suppose: a record says "This Level-2 (L2) dataset". Then: the instance is "Level-2 (L2)", with no ALSO_KNOWN_AS triple.
- Writing a classed triple, rule 20: Parentheses that hold the code of something else are not part of the instance. Suppose: a record says "This data set contains Level 2/3 (EDR/RDR) data" and "The RDR data convert the EDR (raw) sensor data". Then: the record uses "EDR" and "RDR" as names of the data, not of the levels, so the levels are "Level 2" and "Level 3": "EDR (raw) sensor data" HAS_PROCESSING_LEVEL "Level 2", and "RDR data" HAS_PROCESSING_LEVEL "Level 3". Write ALSO_KNOWN_AS only when the record gives the other name in words of its own
- Writing a classed triple, rule 23: One thing, one wording, within a record. When a record names the same thing more than once, in different words, use the first wording this order picks; the others appear only in an ALSO_KNOWN_AS triple, and only if the record states one (rule 20). 1. The wording that says more: it contains the other's words, each as a whole word, is more precise, or spells out the other's abbreviation. 2. Otherwise, the wording from a sentence that states a fact about the thing with words for its predicate, rather than one that names it only by a title's or a name's words (rule 17, A title's facts, A name's facts). 3. Otherwise, the wording the record uses most often. 4. Otherwise, the wording the record gives first.

### Consequences

#### Option 1: Another name of the version (as now)

- Nothing changes.
- The datasets of one Collection are joined only by the words of their ALSO_KNOWN_AS triples, so a search for all the datasets of Collection 6.1 has to search those words.

#### Option 2: Something the dataset belongs to

- A new entity class and predicate in the ground truth schema, and an example for them in the annotation guidelines; the [model](../docs/terminology.md#8-the-pipeline) follows the same rules, so its copy of the rules changes too.
- The ground truth triple "Version 61" (Version) ALSO_KNOWN_AS "Collection 6.1" (Version) is replaced by one joining the dataset to the Collection.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_VERSION "V2019.0" (Version)
- classed triple of the record at pool position 4: "V2019.0" (Version) SUPERSEDES "v2014.1" (Version)
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_VERSION "Version 61" (Version)
- classed triple of the record at pool position 2: "Version 61" (Version) ALSO_KNOWN_AS "Collection 6.1" (Version)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_VERSION "Version 6" (Version)
- classed triple of the record at pool position 7: "Version 6.1" (Version) SUPERSEDES "Version 6" (Version)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_VERSION "V1.0" (Version)
- classed triple of the record at pool position 13: "V1.0" (Version) ALSO_KNOWN_AS "first version" (Version)
- translation table row: predicate SUPERSEDES
- ground truth schema entry: predicate SUPERSEDES
- rule: What counts as a fact, rule 10
- rule: Writing a classed triple, rule 20
- rule: Writing a classed triple, rule 23

## Q20: What counts as an identifier ("MCD19A2N", "LAWRENCEETAL2013"), and is "MCD19A1N" another dataset?

- status: withdrawn
- priority: low
- question kind: records and triples
- in short: the ground truth schema's Identifier, HAS_DOI, Document, Version and COMPUTED_FROM, the predicate HAS_IDENTIFIER we have coined, and rules 20, 21 and 24 of *Writing a classed triple* in the annotation guidelines

### The question

The example below, a MODIS aerosol product, has two passages we are not sure how to write as facts. We would like to know:

- (a) "(MCD19A2N)": we wrote it as an identifier of the dataset, an Identifier being "a code that names one thing, or one product line, permanently, e.g. a DOI; MOD11A1". Is a NASA product short name such as MCD19A2N permanent in that sense, or a label that can change, or be given to another product later? Another record, "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006", uses one short name for two versions, "MOD11A1 Version 6" and "MOD11A1 Version 6.1": is a short name that two versions share an identifier of each of them, or of the product across its versions?
- (b) "The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product": is the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) (the MCD19A1N product) another product, computed from this one, as we wrote?

### Example record

- record id: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- pool position: 6
- title: MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid
- notes: The Moderate Resolution Imaging Spectroradiometer (MODIS) Near Real Time (NRT) Combined Terra and Aqua Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth gridded Level 2 product (MCD19A2N) produced daily at 1 kilometer (km) pixel resolutions. The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product.
- source text: gridded Level 2 product (MCD19A2N)
- source text: The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product
- source text: The MCD19A2N product provides the atmospheric properties and view geometry
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_IDENTIFIER "MCD19A2N" (Identifier)
- classed triple: "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "atmospheric properties" (PhysicalQuantity)
- classed triple: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_ANCILLARY_DATA "view geometry" (Variable)

### Ground truth schema

- entity class Identifier: a code that names one thing, or one product line, permanently, e.g. a DOI; MOD11A1
- predicate COMPUTED_FROM: was made by processing this input

### Options

#### Option 1: Write neither for now

Neither (a) nor (b) is written as a fact for now: the record keeps only its other facts.

#### Option 2: Write each with what the ground truth schema has

With the relationships our schema already has: (a) MCD19A2N written as another name of the dataset, not as an identifier; (b) the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) written as made from this dataset.

#### Option 3: A predicate of its own for an identifier

The dataset has the identifier "MCD19A2N", with the predicate HAS_IDENTIFIER we coined, as we wrote it; (b) as you answer it.

### My current reading

Undecided. For (a), we lean towards option 3, an identifier, since a product code names one product, or one product line, permanently, much as a DOI does. For (b), we write that the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) is made from this dataset, since our rules always write how two datasets are connected, and leave out what it holds, since it is another dataset.

### My notes

The example is the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid", in the ground truth now: the triple with HAS_IDENTIFIER is written so for now. "Near Real Time (NRT)" has no classed triple until (a) is answered. The record titled "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid NRT" is not in our ground truth candidates pool. (d) is about the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0", only named in the question; its classed triple is listed under Affects. Until an expert answers (d), its ground truth keeps LAWRENCEETAL2013 a Document.

Pending facts, for the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid":

- pending fact: its fact 11, "Near Real Time (NRT)", left without a fact for now; added if the answer to (a) says what it is (a latency, a processing stream or a version), with the predicate that answer calls for.
- its fact 12, "MCD19A1N" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset): no longer pending, a ground truth triple now (decided 2026-10-25), by rule 21 of *Writing a classed triple* ("In every case, include the connection the record states"); deleted if the answer to (c) says it is a fact about the other dataset only. What MCD19A1N holds stays left out (`annotations/left_out.md`).
- "atmospheric properties" and "view geometry": written as its fact 13, two HAS_MEASUREMENTS_OF triples (approved 2026-10-25); their doubts are Q3 (b) (formerly Q3 (g)).

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was. The sub-questions (a) to (c) keep their letters, shortened. Left for us: whether HAS_DOI and HAS_IDENTIFIER should be one predicate, and how to write a DOI given as a link address (from the old (b)), which follow from the answer to (b); whether "MCD19A1N is computed from this dataset" is a fact to write (from the old (c)), which our rule 21 settles; and the old (d), on LAWRENCEETAL2013, which the ground truth schema's definition of Document settles for now (it names LAWRENCEETAL2013 as its example). The question's title still names LAWRENCEETAL2013, as comments may be filed under it.

- The question, as it was: We are annotating a record of a MODIS aerosol product, and three passages of its [text](../docs/terminology.md#1-records-and-their-text) we are not sure how to write as classed triples; one of them raises a question about another record too:
- (a) "Near Real Time (NRT)": is it a latency (how soon after the observation the data are made available), a separate processing stream (a different product from the standard one), or a version? Each would be a different predicate, and the ground truth schema has none for a latency. Until you answer, we write no classed triple for it.
- (b) "(MCD19A2N)": we have written it as an identifier of the dataset, with a predicate we coined for it, HAS_IDENTIFIER, "has this Identifier": the dataset HAS_IDENTIFIER "MCD19A2N" (Identifier), an Identifier being "a code that names one thing permanently, e.g. a DOI". Is a NASA product short name such as MCD19A2N permanent in that sense, or a label that can change, or be given to another product later? And should HAS_DOI ("has the Digital Object Identifier") and HAS_IDENTIFIER be one predicate, a DOI being one sort of identifier, or stay two? The record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" names its product "MOD11A1 Version 6", and the one users are encouraged to use instead "MOD11A1 Version 6.1": one short name for two versions. We wrote "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_IDENTIFIER "MOD11A1" (Identifier). Is a short name that two versions share an identifier of each of them, or of the product across its versions? The same record gives its input's DOI as a link address, which we wrote as written: "MOD11_L2" (Dataset) HAS_DOI "https://doi.org/10.5067/MODIS/MOD11_L2.006" (Identifier).
- (c) "The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product": is "MCD19A1N" another dataset? If it is, is "MCD19A1N is computed from this dataset" a fact to write, as we now do (it says how the two datasets are connected), or a fact about the other dataset, to leave out? And are "the atmospheric properties and view geometry" what this dataset holds, to write as facts about it, or only the part of it the other product uses? (Whether each is specific enough, and what kind of thing each is, is asked in another question, about what is measured and what is computed.)
- (d) The same question of what counts as an identifier, in another record: the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" says "Details of the map and data reduction are described in LAWRENCEETAL2013". We wrote LAWRENCEETAL2013 as a Document, "a written publication, or a set of them, named in words or by a reference key": "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) DOCUMENTED_AT "LAWRENCEETAL2013" (Document). Is a Planetary Data System reference key such as LAWRENCEETAL2013 the publication itself (a Document named by its key, as now), or an identifier of the publication, an Identifier of its own?

The question's context, as it was: Below are the facts we have written for this record, now in the ground truth; one of them is "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_IDENTIFIER "MCD19A2N" (Identifier), which (b) asks about. We have written no fact for "Near Real Time (NRT)" until (a) is answered. For (c), we have written "MCD19A1N" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset), and left out what MCD19A1N holds (rule 21, quoted below).

What we have checked about (a), on 2026-10-25. NASA's LANCE page (https://www.earthdata.nasa.gov/data/projects/lance) said then: "Near real-time (NRT) refers to data available 1 to 3 hours after an observation by an instrument aboard a space-based platform" (on 2026-10-30 the page read instead "makes NASA Earth observation data available within three hours of a satellite observation"; NASA's metadata standard UMM-C still defines NEAR_REAL_TIME as 1 to 3 hours after data acquisition); the Terra, Aqua and Aura measurements "are processed into higher-level "standard" products within 8 to 40 hours of observation"; and "If latency is not a primary concern, users are encouraged to use standard science products, which are created using the best available ancillary, calibration, and ephemeris information". MODAPS lists MCD19A2N among its Collection 6.1 NRT products, as a product of its own, with its own DOI, 10.5067/MODIS/MCD19A2N.NRT.061 (https://modaps.modaps.eosdis.nasa.gov/services/about/products/c61-nrt/MCD19A2N.html), apart from the standard product MCD19A2. So our reading of the sources: NRT here names a processing stream, a separate product, whose defining property is how soon it is made available. The record itself states no number of hours, and the annotation guidelines write only what the record states, so a latency value from these sources can't go into its ground truth. The catalog also has another record, titled "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid NRT", whose notes begin with the same words as this record's.

The example, as it was, also had these source texts and classed triples (all in the ground truth of the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid"): source texts "The Moderate Resolution Imaging Spectroradiometer (MODIS)", "Combined Terra and Aqua", "Land Aerosol Optical Depth", "produced daily", "gridded Level 2 product", "at 1 kilometer (km) pixel resolutions" and "Multi-Angle Implementation of Atmospheric Correction (MAIAC) Land Aerosol Optical Depth"; classed triples "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument); FROM_SPACECRAFT "Terra" (Spacecraft); FROM_SPACECRAFT "Aqua" (Spacecraft); HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity); HAS_SPATIAL_COVERAGE "Land" (SpatialExtent); HAS_TEMPORAL_RESOLUTION "daily" (TemporalResolution); HAS_PROCESSING_LEVEL "Level 2" (ProcessingLevel); HAS_SPATIAL_REPRESENTATION "gridded" (SpatialRepresentation); HAS_SPATIAL_RESOLUTION "1 kilometer (km)" (SpatialResolution); PRODUCED_USING_ALGORITHM "Multi-Angle Implementation of Atmospheric Correction (MAIAC)" (Algorithm); each with the dataset "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" as its subject instance. The example now shows only the passages (a) to (c) are about.

The options, as they were: Option 2: (a) "Near Real Time (NRT)" kept inside the dataset's description, with no fact of its own; (b) "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) ALSO_KNOWN_AS "MCD19A2N", in place of HAS_IDENTIFIER, and HAS_DOI as it is; (c) "MCD19A1N product" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset), as a processing step of rule 24 with this dataset as its input. Option 3: A new predicate for a latency (the dataset has the latency "Near Real Time (NRT)"), and the one we coined for an identifier kept (the dataset HAS_IDENTIFIER "MCD19A2N" (Identifier)), both in the ground truth schema, with HAS_DOI either kept or made one with HAS_IDENTIFIER (question (b)); (c) and (d) as you answer them.

The current reading, as it was: Undecided. For (a), we lean towards reading NRT as a processing stream, a product of its own (the sources above), with no latency value, since the record states none. For (b), we lean towards option 3, an identifier, since a product code names one product permanently, much as a DOI does. For (c), we write "MCD19A1N" COMPUTED_FROM this dataset, by rule 21 ("In every case, include the connection the record states"), and leave out what MCD19A1N holds, since it is made from this dataset. For (d), we keep LAWRENCEETAL2013 a Document, as the definition of Document names it. We would still like to know whether MCD19A1N is computed from this product, and whether "the atmospheric properties and view geometry" are what this dataset holds.

Decided on 2026-10-31, so the old (a) is no longer asked: "Near Real Time (NRT)" is a latency, how soon the data are released after observation. The ground truth schema has a new entity class Latency ("a measure of how soon data are released after observation, e.g. Near Real Time (NRT)") and a new predicate HAS_LATENCY ("is released this soon after observation"), and the record has "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_LATENCY "Near Real Time (NRT)" (Latency), in the record's words; the pending fact 11 above is written so. Field practice: NASA's metadata standard UMM-C records it in a closed field, CollectionDataType (NEAR_REAL_TIME, LOW_LATENCY, EXPEDITED, SCIENCE_QUALITY), whose NEAR_REAL_TIME is "ready for end user consumption 1 to 3 hours after data acquisition" (UMM-C JSON schema v1.18.7, https://github.com/nasa/Common-Metadata-Repository/blob/master/umm-spec-lib/resources/json-schemas/collection/umm/v1.18.7/umm-c-json-schema.json); the record states no number of hours, so none is written. The pending fact's other readings, a processing stream or a version, are not written.

Changed on 2026-10-31, for the old (c), now the expert's (b): the subject of fact 12 is now "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" (Dataset), the wording the record gives first (rule 23), in place of "MCD19A1N": "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset). The ground truth schema's Identifier now reads "a code that names one thing, or one product line, permanently, e.g. a DOI; MOD11A1"; the expert's (a) quotes it so.

Taken out of the expert's view on 2026-10-31, as questions we can settle from sources or have decided; kept here word for word. The title was "What is "Near Real Time (NRT)", what counts as an identifier ("MCD19A2N", "LAWRENCEETAL2013"), and is "MCD19A1N" another dataset?". The expert's (a) is the old (b), and their (b) the first half of the old (c); the options, my current reading and the consequences say "(a)" and "(b)" for them. The second half of the old (c) is settled from sources: the MAIAC user guide lists what MCD19A2 holds, aerosol optical depth, water vapour and the other atmospheric properties, and "View Geometry over land and water at 5km: Cosines of Solar and View zenith angles, relative azimuth, scattering angle and glint angle" (Lyapustin and Wang, LP DAAC, https://lpdaac.usgs.gov/documents/1500/MCD19_User_Guide_V61.pdf, section 3.2.1), so "the atmospheric properties and view geometry" are the whole of what this dataset holds, as the ground truth writes them.

- The question's opening, as it was: The example below, a MODIS aerosol product, has three passages we are not sure how to write as facts. We would like to know:
- (a) "Near Real Time (NRT)": what is it, for this dataset? Our reading of NASA's own pages (checked, below) is that NRT data are a separate product, made available within hours of the observation, apart from the standard product made later. Is NRT then a fact worth recording about a dataset (a kind of product, a version), or only how soon the data come? Until you answer, we write nothing for it.
- (b) "(MCD19A2N)": we wrote it as an identifier of the dataset, an Identifier being "a code that names one thing permanently, e.g. a DOI". Is a NASA product short name such as MCD19A2N permanent in that sense, or a label that can change, or be given to another product later? Another record, "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006", uses one short name for two versions, "MOD11A1 Version 6" and "MOD11A1 Version 6.1": is a short name that two versions share an identifier of each of them, or of the product across its versions?
- (c) "The MCD19A2N product provides the atmospheric properties and view geometry used to calculate the MAIAC Land Surface Bidirectional Reflectance Factor (BRF) or surface reflectance, MCD19A1N product": is MCD19A1N another product, computed from this one, as we wrote? And are "the atmospheric properties and view geometry" what this dataset holds, or only the part of it that the other product uses?
- The question's context, as it was: What we checked about (a), on 2026-10-25. NASA's LANCE page (https://www.earthdata.nasa.gov/data/projects/lance) said then: "Near real-time (NRT) refers to data available 1 to 3 hours after an observation by an instrument aboard a space-based platform" (on 2026-10-30 the page read instead "makes NASA Earth observation data available within three hours of a satellite observation"; NASA's metadata standard UMM-C still defines NEAR_REAL_TIME as 1 to 3 hours after data acquisition), and that the standard products are made "within 8 to 40 hours of observation". NASA's MODAPS lists MCD19A2N as a product of its own, with its own DOI, apart from the standard product MCD19A2 (https://modaps.modaps.eosdis.nasa.gov/services/about/products/c61-nrt/MCD19A2N.html). The record itself states no number of hours, and we write only what a record states.
- The example also showed the source text "Near Real Time (NRT)", and the classed triple "MCD19A1N" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset).
- Option 1, "Write none of the three for now", as it was: None of (a), (b), (c) is written as a fact for now: the record keeps only the facts written so far.
- Option 2, as it was: With the relationships our schema already has: (a) "Near Real Time (NRT)" kept inside the dataset's description, with no fact of its own; (b) MCD19A2N written as another name of the dataset, not as an identifier; (c) MCD19A1N written as made from this dataset.
- Option 3, "New predicates for a latency and an identifier", as it was: Two new relationships: the dataset has the latency "Near Real Time (NRT)", and the dataset has the identifier "MCD19A2N", as we wrote it; (c) as you answer it.
- My current reading, as it was: Undecided. For (a), we lean towards reading NRT as a separate product of its own (the sources above), with no number of hours, since the record states none. For (b), we lean towards option 3, an identifier, since a product code names one product permanently, much as a DOI does. For (c), we write that MCD19A1N is made from this dataset, since our rules always write how two datasets are connected, and leave out what MCD19A1N holds, since it is another dataset.
- The consequences, as they were: option 1, "The facts the three passages may state are missing from the ground truth: an extracted triple that states one of them counts as wrong when this record is evaluated."; option 2, "- (c) writes a fact whose subject instance is another dataset, which rule 21 may forbid (question (c))."; option 3, "Two new predicates in the ground truth schema, each with a definition and an example in the annotation guidelines; the [model](../docs/terminology.md#8-the-pipeline) follows the same rules, so its copy changes too." and "Other records with a product code or a latency are written the same way.". Under Affects: "pipeline method: annotations/ground_truth_schema.txt: a new predicate for a latency and one for an identifier (option 3)".

Withdrawn on 2026-10-31: settled from sources, so it is no longer asked of the experts; kept whole, so that comments filed under its number still find it. (a): a NASA short name names a product line across its versions, the short name and the version together name one collection, and the DOI is per version (research G10 of 2026-10-30, above); MCD19A2N's version is "6.1NRT" and its DOI 10.5067/MODIS/MCD19A2N.NRT.061 (NASA CMR, https://cmr.earthdata.nasa.gov/search/collections.umm_json?short_name=MCD19A2N). Identifier's definition already reads "a code that names one thing, or one product line, permanently" (decided on 2026-10-31, research B6), so "MCD19A2N" and "MOD11A1" stay HAS_IDENTIFIER (option 3). (b): the record's words are true as worded. In one MAIAC run, "Following cloud detection and aerosol retrieval, the atmospheric correction derives surface spectral BRF and BRDF models", with a surface term "computed using the current RTLS parameters and retrieved aerosol data" (Lyapustin, Wang, Korkin and Huang, "MODIS Collection 6 MAIAC algorithm", *Atmospheric Measurement Techniques* 11, 5741–5765, 2018, https://doi.org/10.5194/amt-11-5741-2018, section 9), and the run writes both files (section 10). So the BRF is computed from the values the record's dataset holds, and "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" COMPUTED_FROM the record's dataset stays (rule 21); no source says that the BRF processing reads the MCD19A2 files themselves (my reading of the sources searched), and the processing chain is for 080's enrichment.

### Quoted for us

- predicate HAS_DOI: has this Identifier, a Digital Object Identifier
- entity class Document: a written publication, or a set of them, named in words or by a reference key, e.g. NASA developed standards; LAWRENCEETAL2013
- predicate DOCUMENTED_AT: more details about it are written at this WebPage or in this Document
- entity class Version: a label that marks one release of something
- predicate ALSO_KNOWN_AS: is the same thing under another name
- predicate HAS_LATENCY -> (none): The subject (a data product or table) is made available or updated with the object, a latency or update delay.
- predicate HAS_IDENTIFIER -> (none): The subject (a dataset, data series or document) is indexed by, or refers to items using, the object, which is a key, label or designator such as a prime key or detector name.
- What counts as a fact, rule 1: Only what the record states. Never add what you know from elsewhere, and never write down what an unexplained code or abbreviation stands for.
- Writing a classed triple, rule 20: A name with its own abbreviation, another name or code of its own, or a short note in parentheses is one instance, as written.
- Writing a classed triple, rule 21: General facts: include them; about another dataset, only when the record links it to the record's dataset by "part of" or "made from".
- Writing a classed triple, rule 21: Another dataset. Include facts about another dataset when the record states a chain of "part of" or "made from" links that connects it to the record's dataset: its parts, what it is part of, what it is made from, and so on through further datasets or variables the record names. Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it. In every case, include the connection the record states (rule 1 of What counts as a fact: only what the record states).
- Writing a classed triple, rule 24: A processing step: output = method(input).

### Consequences

#### Option 1: Write neither for now

- The facts the two passages may state are missing from the ground truth: an extracted triple that states one of them counts as wrong when this record is evaluated.
- Nothing in the ground truth schema or the annotation guidelines changes.

#### Option 2: Write each with what the ground truth schema has

- No new entity class or predicate.
- (b) treats a product code as another name, which rule 20 of *Writing a classed triple* doesn't cover (it covers an abbreviation in parentheses, and MCD19A2N doesn't abbreviate the words before it).
- (b) writes a fact whose subject instance is another dataset, which rule 21 may forbid (question (b)).

#### Option 3: A predicate of its own for an identifier

- A predicate of its own for an identifier in the ground truth schema, HAS_IDENTIFIER, with a definition and an example in the annotation guidelines; the [model](../docs/terminology.md#8-the-pipeline) follows the same rules, so its copy changes too.
- Other records with a product code are written the same way.

### Affects

- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_IDENTIFIER "MCD19A2N" (Identifier)
- classed triple of the record at pool position 6: "MAIAC Land Surface Bidirectional Reflectance Factor (BRF)" (Dataset) COMPUTED_FROM "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_LATENCY "Near Real Time (NRT)" (Latency)
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- classed triple of the record at pool position 2: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD02HKM.061" (Identifier)
- classed triple of the record at pool position 2: "radiance data" (Dataset) HAS_DOI "DOI:10.5067/MODIS/MYD021KM.061" (Identifier)
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) DOCUMENTED_AT "LAWRENCEETAL2013" (Document)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_IDENTIFIER "MOD11A1" (Identifier)
- classed triple of the record at pool position 7: "MOD11_L2" (Dataset) HAS_DOI "https://doi.org/10.5067/MODIS/MOD11_L2.006" (Identifier)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) HAS_IDENTIFIER "VNP43D12" (Identifier)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_IDENTIFIER "H3ZFCGPH" (Identifier)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_IDENTIFIER "DSWx-S1" (Identifier)
- ground truth schema entry: entity class Identifier
- ground truth schema entry: predicate HAS_DOI
- ground truth schema entry: entity class Latency
- ground truth schema entry: predicate HAS_LATENCY
- translation table row: entity class DOI
- translation table row: predicate HAS_DOI
- translation table row: predicate HAS_LATENCY
- translation table row: predicate HAS_IDENTIFIER
- rule: What counts as a fact, rule 1
- rule: Writing a classed triple, rule 20
- rule: Writing a classed triple, rule 21
- rule: Writing a classed triple, rule 24
- pipeline method: annotations/ground_truth_schema.txt: a predicate of its own for an identifier (option 3)
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

## Q21: Should instruments, spacecraft, missions and physical quantities follow a reference list, and what should the knowledge graph answer?

- status: open
- priority: low
- question kind: general
- in short: reference lists for the ground truth schema's Instrument, Spacecraft, Mission and PhysicalQuantity, and the questions the knowledge graph is for

### The question

We write every fact in the record's own words. So two records that name one instrument in two ways ("Moderate Resolution Imaging Spectroradiometer (MODIS)" in one, "MODIS" in another) give two different names in the knowledge graph. Published lists of standard names exist for instruments, spacecraft, missions and measured quantities, and a record's words could be matched to them: for missions we already have one in mind, for processing levels a list that records each value's scheme (the question on processing levels), and the Global Change Master Directory (GCMD) Keywords for the others. We would like to know:

- (a) For missions, we plan to match a record's words to NASA's own list. NASA's mission pages have two views: the *A to Z List* (https://www.nasa.gov/a-to-z-of-nasa-missions/, 664 entries, what NASA calls missions, among them "Aqua", "Terra", "Dawn" and "Aquarius"; by our definition of a mission, "a named spaceflight effort", a few entries are other things, such as "LIS (Lightning Imaging Sensor)", "Voyager Program" beside "Voyager 1", or "Advanced Spacesuits"), and *Science Missions* (https://science.nasa.gov/science-missions/, about 450 entries, which can be filtered by status, type, target and program, each with a one-line description). The catalog also names other agencies' missions: Rosetta, an ESA mission, is in the A to Z List only as "Rosetta-Philae". We also found lists by field: GCMD's Projects hold Earth science missions such as "Aqua" and "Terra", but not Rosetta, Dawn or Stardust, and the Planetary Data System's list of investigations holds "INTERNATIONAL ROSETTA MISSION" and "DAWN MISSION TO VESTA AND CERES". Which of these, or which other list, should be the list of missions for this catalog: one list for all, or one per field, with the A to Z List for the rest?
- (b) For instruments, spacecraft and measured quantities, the list we know of is the Global Change Master Directory (GCMD) Keywords, "a hierarchical set of controlled Earth Science vocabularies", with lists of Instruments/Sensors, Platforms/Sources, Projects, and Measurement Names, among others (https://www.earthdata.nasa.gov/data/tools/gcmd-keyword-viewer). For the planetary records, the Planetary Data System keeps its own list, its context products (one entry for each investigation, instrument host, instrument and target, with the archive's other names for it); for the heliophysics records, SPASE defines observatories and instruments (SPASE 2.7.1, https://spase-group.org/data/model/spase-2.7.1.pdf). GCMD's planetary names can mislead: its "RSI" is a "Remote Sensing Instrument" and its "OSIRIS" an instrument of the Odin satellite, while Rosetta has instruments with the same short names. Is GCMD the right list for the Earth science records, are those two the right ones for the planetary and heliophysics records, and which list has the same standing for the astrophysics records?
- (c) What questions should a knowledge graph of this catalog be able to answer for you? For example: "Which datasets were collected by MODIS aboard Aqua at Level 3?", or "Which datasets cover the Arctic every day?". Your questions decide which facts matter most.

### Options

#### Option 1: The record's own words everywhere (as now)

Every name stays as the record writes it, and no reference list is used.

#### Option 2: Reference lists in the ground truth

For instruments, spacecraft, missions and measured quantities, we write the reference list's name that the record's words mean, in place of the record's words.

#### Option 3: Own words in the ground truth, reference lists added later

Each record keeps its own words; the reference list's names are added to the knowledge graph later, next to the record's words.

### My current reading

Undecided, leaning towards option 3, because it keeps what we write close to what each record states, and still lets the knowledge graph use a reference list. We would choose option 2 for a kind of thing whose names you say form a short, closed list.

### My notes

Checked on 2026-10-26 by fetching the pages: NASA's mission pages have two views, the *A to Z List* (https://www.nasa.gov/a-to-z-of-nasa-missions/, 664 entries) and *Science Missions* (https://science.nasa.gov/science-missions/, about 450 entries, filterable by status, type, target and program, each with a one-line description, e.g. "Aqua is a NASA Earth Science satellite mission that is collecting data about the Earth's water cycle."). The A to Z List's entries are what NASA calls missions; by our Mission definition ("a named spaceflight effort") a few are other things, e.g. "LIS (Lightning Imaging Sensor)", "Voyager Program" beside "Voyager 1", "Expedition 1" and the other expeditions, "Advanced Spacesuits". Rosetta appears only as "Rosetta-Philae". docs/improvements.md, *Linking subject instances and object instances to reference lists*, plans the A to Z List for missions (a subject or object instance with no match marked for a person to check, since the catalog also names other agencies' missions), the processing levels L0, L1A, L1B, L2, L3, L4 first, and GCMD keywords as another list.

Linking instances to reference lists is on our list of improvements to the pipeline (quoted below, under Pipeline method), as a later stage that keeps each record's own words.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as it was.

The question's opening, as it was: The ground truth writes each subject instance and object instance in the record's own words. For the instruments, spacecraft, missions and physical quantities of the ground truth schema, published lists of values exist, and a record's words could be checked against them, or replaced by them.

The old (a), as it was (now the expert's (a), on missions, and (b), on the other kinds of thing; the old (b) is now (c)): Which reference list do people in your field rely on for a dataset's instrument, spacecraft, mission and measured quantity? The one we know of is the Global Change Master Directory (GCMD) Keywords, "a hierarchical set of controlled Earth Science vocabularies", with lists of Instruments/Sensors, Platforms/Sources, Projects, and Measurement Names, among others (https://www.earthdata.nasa.gov/data/tools/gcmd-keyword-viewer). Is it the right one for this catalog, and is there a list of the same standing for the planetary, astrophysics and heliophysics records, whose missions and instruments are beyond Earth science?

The end of the old (b), as it was: Your questions decide which facts matter most, and so which entity classes and predicates the ground truth schema needs.

The question's context, as it was: The knowledge graph will be built from the records' metadata fields and the extracted triples. Two records that write one thing in two wordings (e.g. "Moderate Resolution Imaging Spectroradiometer (MODIS)" and "MODIS") give two different instances; a reference list would give one.

The options, as they were: Option 1: Every subject instance and object instance stays as the record writes it, and no reference list is used. Option 2: For Instrument, Spacecraft, Mission and PhysicalQuantity, the instance is the reference list's value that the record's words mean, in place of the record's words. Option 3: Each record keeps its own words; the values on a reference list are added to the knowledge graph later, next to the record's words.

Changed on 2026-10-31, under Affects: the record "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" no longer has "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument) (rule 1 of *What counts as a fact*: the record doesn't explain the code, so its entity class isn't written either; see Q10); and the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" has "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) HAS_NUMBER_OF "36 spectral bands" (Value), in place of HAS_SPECTRAL_BANDS, which the ground truth schema merged into HAS_NUMBER_OF ("has this many").

My current reading, as it was: Undecided, leaning towards option 3, because it keeps the ground truth close to what each record states, and still lets the knowledge graph use a reference list. We would choose option 2 for an entity class whose values an expert says form a short, closed list.

Changed on 2026-10-31, so that the opening matches the decision of that day on processing levels (research B1, docs/improvements.md, *Linking subject instances and object instances to reference lists*); the opening said, word for word: "for processing levels a short list of our own (the question on processing levels)".

Checked on 2026-10-31, for the expert's (c): the method's standard is that competency questions come from users' scenarios (Grüninger and Fox, "Methodology for the Design and Evaluation of Ontologies", IJCAI-95 workshop; not read in full), and a study of dataset search logs and data requests found place, time and the granularity the user needs among the most common features asked for (Kacprzak, Koesten, Ibáñez, Blount, Tennison and Simperl, "Characterising dataset search—An analysis of search logs and data requests", *Journal of Web Semantics* 55, 2019; its abstract only, strong secondary). The examples in (c) already lead with these.

Changed in the expert's view on 2026-10-31 (the research of 2026-10-31 on NASA's reference lists), so that (a) and (b) name the lists we found per field; kept here word for word. (a) ended: "Which of the two views, or which other list, should be the list of missions for this catalog?" (b) was: "- (b) For instruments, spacecraft and measured quantities, the list we know of is the Global Change Master Directory (GCMD) Keywords, "a hierarchical set of controlled Earth Science vocabularies", with lists of Instruments/Sensors, Platforms/Sources, Projects, and Measurement Names, among others (https://www.earthdata.nasa.gov/data/tools/gcmd-keyword-viewer). Is it the right one for this catalog, and is there a list of the same standing for the planetary, astrophysics and heliophysics records, whose instruments and spacecraft are beyond Earth science?"

Checked on 2026-10-31, for (a) and (b): no one NASA list covers the catalog. GCMD's Projects (2,110 entries) and Platforms have no Rosetta, Dawn or Stardust; its Interplanetary Spacecraft category has 10 entries, e.g. VOYAGER 1 and LRO. The Planetary Data System's context products (https://pds.nasa.gov/data/pds4/context-pds4/, file lists of 2026-10-31, versions counted) hold 368 investigation files (264 of them missions, other agencies' included), 416 instrument hosts, 2,721 instruments and 3,409 targets, each with a type, a description and the PDS3 names as other names ("INTERNATIONAL ROSETTA MISSION" and "ROSETTA"; "DAWN MISSION TO VESTA AND CERES" and "DAWN"; "MARS EXPRESS" and "MEX"). SPASE defines an Instrument as "A device that makes measurements used to characterize a physical phenomenon, or a family of like devices"; its registry was not checked (its host now serves a parked page). NSSDCA's master catalog could not be fetched. GCMD's "RSI | Remote Sensing Instrument" (a camera) and "OSIRIS | Optical Spectrograph and Infrared Imaging System" (Odin) share their short names with Rosetta's instruments, so a match by name alone would link planetary instruments wrongly: docs/improvements.md, *Linking subject instances and object instances to reference lists* (080), now says a match must use the record's domain. Astrophysics lists were not researched.

### Quoted for us

- Writing a classed triple, rule 11: Subject instance and object instance: the record's own words, as written.

### Consequences

#### Option 1: The record's own words everywhere (as now)

- Nothing changes in the annotation guidelines or the ground truth schema.
- One value may appear in several wordings across records, so a search of the knowledge graph has to know each wording.

#### Option 2: Reference lists in the ground truth

- A new exception to rule 11 of *Writing a classed triple* (the record's own words, as written), in the annotation guidelines and in the copy of the rules the [model](../docs/terminology.md#8-the-pipeline) follows.
- The ground truth triples written so far are checked again, and some object instances change.
- A record's value that isn't on the list has no value to use, unless the list is complete for this catalog.

#### Option 3: Own words in the ground truth, reference lists added later

- The annotation guidelines and the ground truth don't change, and the knowledge graph can still be searched by a list's values.
- Work to match each wording to a list's value, outside the ground truth: on our list of improvements, not built yet.

### Affects

- record at pool position 1: cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc
- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 5: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 10: 3bceffb4-f01e-433c-af79-42b9d9427231
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 16: ec41fd5d-1159-4aa8-9803-5346e2324a20
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- record at pool position 21: 264a9b23-9a86-46a7-ab61-9661230ea667
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 22: 967275c7-aa2d-4b08-a9db-aff5cf6b7802
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- record at pool position 15: 32614a2f-a286-4c7c-9f1e-deafdf8bd6a3
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_PLATFORM "Terra" (Platform)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "Aerosol Optical Depth" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_MEASUREMENTS_OF "atmospheric properties" (PhysicalQuantity)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_ANCILLARY_DATA "view geometry" (Variable)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "radiance data" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 2: "Moderate Resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Platform)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) ACQUIRED_BY_INSTRUMENT "Aquarius L-band radiometer" (Instrument)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 4: "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) ABOARD "Aqua" (Platform)
- classed triple of the record at pool position 4: "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument) HAS_NUMBER_OF "36 spectral bands" (Value)
- classed triple of the record at pool position 4: "mid-infrared 3.95 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 4: "mid-infrared 4.05 micron wavelength channel" (Channel) UNIQUE_TO_INSTRUMENT "Moderate-resolution Imaging Spectroradiometer (MODIS)" (Instrument)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND plus Z boron loaded sensor" (Instrument)
- classed triple of the record at pool position 5: "GRaND plus Z boron loaded sensor" (Instrument) PART_OF "GRaND" (Instrument)
- classed triple of the record at pool position 5: "GRaND epithermal neutron map" (Dataset) ACQUIRED_BY_INSTRUMENT "GRaND" (Instrument)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_PLATFORM "ROSETTA-ORBITER" (Platform)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) FROM_PLATFORM "Aqua" (Platform)
- classed triple of the record at pool position 4: "Aqua" (Platform) LAUNCHED_BY_PARTY "NASA" (Organization)
- classed triple of the record at pool position 4: "Aqua" (Platform) LAUNCHED_ON "May 4, 2002" (Time)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_ORBIT "sun synchronous, polar orbit with a daylight ascending node at 13:30" (Orbit)
- classed triple of the record at pool position 4: "Aqua" (Platform) FLIES_IN "A-train" (SatelliteFormation)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the atmosphere" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the land" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_PURPOSE "study the global dynamics of the oceans" (Purpose)
- classed triple of the record at pool position 4: "Aqua" (Platform) HAS_TARGET "Earth" (CelestialBody)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) FROM_PLATFORM "DAWN" (Platform)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) FROM_MISSION "Rosetta" (Mission)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) FROM_MISSION "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) HAS_VARIABLE "Global Gravity" (Variable)
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_MEASUREMENTS_OF "snow cover" (PhysicalQuantity)
- classed triple of the record at pool position 3: "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" (Dataset) HAS_MEASUREMENTS_OF "Sea Surface Salinity (SSS) retrievals" (PhysicalQuantity)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_MEASUREMENTS_OF "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "skin SST" (Variable) ESTIMATES "skin sea surface temperature (SST)" (PhysicalQuantity)
- classed triple of the record at pool position 4: "SST4" (Variable) ESTIMATES "SST" (PhysicalQuantity)
- classed triple of the record at pool position 5: "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0" (Dataset) RELATED_TO "average atomic mass" (PhysicalQuantity)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) ACQUIRED_BY_INSTRUMENT "MODIS" (Instrument)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) FROM_PLATFORM "Terra" (Platform)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_MEASUREMENTS_OF "Land Surface Temperature" (PhysicalQuantity)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_MEASUREMENTS_OF "Land Surface Emissivity" (PhysicalQuantity)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "quality control assessments" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "observation times" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "view zenith angles" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "clear-sky coverages" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_VARIABLE "band 31 emissivity" (Variable)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_VARIABLE "band 32 emissivity" (Variable)
- classed triple of the record at pool position 7: "band 31 emissivity" (Variable) COMPUTED_FROM "land cover types" (PhysicalQuantity)
- classed triple of the record at pool position 7: "band 32 emissivity" (Variable) COMPUTED_FROM "land cover types" (PhysicalQuantity)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Dust Flux Monitor Instrument (DFMI)" (Instrument)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) FROM_PLATFORM "STARDUST" (Platform)
- classed triple of the record at pool position 9: "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset) FROM_MISSION "Stardust-NExT" (Mission)
- classed triple of the record at pool position 9: "Stardust-NExT" (Mission) ENDED_ON "March, 2011" (Time)
- classed triple of the record at pool position 9: "RDR data" (Dataset) HAS_VARIABLE "dust fluences at each of twelve mass thresholds" (Variable)
- classed triple of the record at pool position 10: "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Rosetta Orbiter ALICE UV Spectrometer" (Instrument)
- classed triple of the record at pool position 10: "Rosetta Orbiter ALICE UV Spectrometer" (Instrument) ABOARD "Rosetta Orbiter" (Platform)
- classed triple of the record at pool position 10: "ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0" (Dataset) FROM_PLATFORM "Rosetta Orbiter" (Platform)
- classed triple of the record at pool position 12: "2XMMi-DR3" (Dataset) FROM_PLATFORM "XMM-Newton" (Platform)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) FROM_PLATFORM "XMM-Newton" (Platform)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_VARIABLE "Ensemble X-Ray Variability" (Variable)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_MEASUREMENTS_OF "redshifts" (PhysicalQuantity)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_MEASUREMENTS_OF "spectral classifications" (PhysicalQuantity)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "OSIRIS Narrow Angle Camera" (Instrument)
- classed triple of the record at pool position 13: "OSIRIS Narrow Angle Camera" (Instrument) ABOARD "ROSETTA-ORBITER" (Platform)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) FROM_PLATFORM "ROSETTA-ORBITER" (Platform)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_SPATIAL_REPRESENTATION "solar stray-light corrected, in-field stray-light corrected, radiometric calibrated and geometric distortion corrected (resampled) image data" (SpatialRepresentation)
- classed triple of the record at pool position 4: "Aqua" (Platform) FLIES_IN "Earth Observation Satellites (EOS)" (SatelliteFormation)
- classed triple of the record at pool position 1: "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "RSI" (Instrument)
- classed triple of the record at pool position 16: "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "PWS spectrum analyzer" (Instrument)
- classed triple of the record at pool position 16: "PWS spectrum analyzer" (Instrument) PART_OF "Plasma Wave Spectrometer (PWS)" (Instrument)
- classed triple of the record at pool position 16: "Plasma Wave Spectrometer (PWS)" (Instrument) ABOARD "Voyager 1" (Platform)
- classed triple of the record at pool position 16: "PWS spectrum analyzer" (Instrument) MEASURES "spectral densities" (PhysicalQuantity)
- classed triple of the record at pool position 16: "PWS spectrum analyzer" (Instrument) HAS_NUMBER_OF "16 frequency channels" (Value)
- classed triple of the record at pool position 16: "PWS spectrum analyzer" (Instrument) HAS_FREQUENCY_RANGE "from 50 Hz to 10 kHz" (Value)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) ACQUIRED_BY_INSTRUMENT "Visible Infrared Imaging Radiometer Suite (VIIRS)" (Instrument)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) ACQUIRED_BY_INSTRUMENT "Rate Counter (RCNT)" (Instrument)
- classed triple of the record at pool position 19: "X-ray spectrometer" (Instrument) ABOARD "BARREL balloon" (Platform)
- classed triple of the record at pool position 19: "X-ray spectrometer" (Instrument) HAS_PURPOSE "measure the bremsstrahlung X-rays produced by precipitating relativistic electrons as they collide with neutrals in the atmosphere" (Purpose)
- classed triple of the record at pool position 19: "DC magnetometer" (Instrument) ABOARD "BARREL balloon" (Platform)
- classed triple of the record at pool position 19: "DC magnetometer" (Instrument) HAS_PURPOSE "measure ULF-timescale variations of the magnetic field" (Purpose)
- classed triple of the record at pool position 19: "BARREL instrumentation" (Instrument) MEASURES "relativistic electron precipitation" (PhysicalQuantity)
- classed triple of the record at pool position 19: "August 2015 BARREL campaign" (Campaign) COORDINATED_WITH "European Incoherent Scatter Scientific Association, EISCAT, incoherent scatter radar system" (Instrument)
- classed triple of the record at pool position 19: "2016 campaign" (Campaign) COORDINATED_WITH "European Incoherent Scatter Scientific Association, EISCAT, incoherent scatter radar system" (Instrument)
- classed triple of the record at pool position 21: "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (Dataset) ACQUIRED_BY_INSTRUMENT "Moon Mineralogy Mapper (M3)" (Instrument)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) ACQUIRED_BY_INSTRUMENT "HIRDLS" (Instrument)
- classed triple of the record at pool position 24: "HIRDLS profiles" (Dataset) ACQUIRED_BY_INSTRUMENT "HIRDLS" (Instrument)
- classed triple of the record at pool position 16: "VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0" (Dataset) FROM_PLATFORM "Voyager 1" (Platform)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) FROM_PLATFORM "NASA/NOAA Suomi National Polar-orbiting Partnership (Suomi NPP)" (Platform)
- classed triple of the record at pool position 19: "BARREL balloon" (Platform) HAS_MASS "approximately 20 kg" (Value)
- classed triple of the record at pool position 22: "Flight Data For Tail 655" (Dataset) FROM_PLATFORM "Tail 655" (Platform)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) FROM_PLATFORM "Aura" (Platform)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) FROM_PLATFORM "Sentinel-1" (Platform)
- classed triple of the record at pool position 25: "Sentinel-1 radar observations" (Dataset) FROM_PLATFORM "Sentinel-1" (Platform)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) FROM_MISSION "BARREL" (Mission)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "study electron losses from Radiation Belts" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_TARGET "Earth" (CelestialBody)
- classed triple of the record at pool position 19: "BARREL" (Mission) PART_OF "NASA Living with a Star" (Organization)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "augment the Radiation Belt Storm Probes, RBSP, mission" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "providing measurements of the spatial variations of electron precipitation from the radiation belts" (Purpose)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_PURPOSE "providing measurements of the temporal variations of electron precipitation from the radiation belts" (Purpose)
- classed triple of the record at pool position 19: "Radiation Belt Storm Probes, RBSP" (Mission) ALSO_KNOWN_AS "Van Allen Probes" (Mission)
- classed triple of the record at pool position 19: "August 2015 BARREL campaign" (Campaign) COORDINATED_WITH "Radiation Belt Storm Probes, RBSP" (Mission)
- classed triple of the record at pool position 19: "2016 campaign" (Campaign) COORDINATED_WITH "Radiation Belt Storm Probes, RBSP" (Mission)
- classed triple of the record at pool position 19: "2013 balloon campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "2014 balloon campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "August 2015 BARREL campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "2016 campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_NUMBER_OF "four BARREL campaigns" (Value)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_NUMBER_OF "over 50 small, approximately 20 kg, stratospheric balloons" (Value)
- classed triple of the record at pool position 19: "BARREL" (Mission) HAS_TIME_SPAN "from 2013 to 2016" (Time)
- classed triple of the record at pool position 21: "CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0" (Dataset) FROM_MISSION "Chandrayaan-1" (Mission)
- classed triple of the record at pool position 21: "Chandrayaan-1" (Mission) HAS_TARGET "Moon" (CelestialBody)
- classed triple of the record at pool position 15: "Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data" (Dataset) HAS_MEASUREMENTS_OF "Heliocentric trajectories" (PhysicalQuantity)
- classed triple of the record at pool position 19: "BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data" (Dataset) HAS_MEASUREMENTS_OF "counts" (PhysicalQuantity)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_MEASUREMENTS_OF "surface water extent over land" (PhysicalQuantity)
- translation table row: entity class Instrument
- translation table row: entity class Spacecraft
- translation table row: entity class SpaceStation
- translation table row: entity class Mission
- translation table row: entity class PhysicalQuantity
- ground truth schema entry: entity class Instrument
- ground truth schema entry: entity class Platform
- ground truth schema entry: entity class Mission
- ground truth schema entry: entity class PhysicalQuantity
- rule: Writing a classed triple, rule 11
- pipeline method: docs/improvements.md: linking subject instances and object instances to reference lists
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

### Pipeline method

- docs/improvements.md: Linking subject instances and object instances to reference lists, so that one thing named several ways ("Aqua", "EOS PM-1") becomes one node.

## Q22: Is a title's "4km" the notes' "4.63 km"?

- status: withdrawn
- priority: low
- question kind: records and triples
- in short: the ground truth schema's SpatialResolution and HAS_SPATIAL_RESOLUTION, and rules 21 and 23 of the annotation guidelines

### The question

The title of the example below says "4km", and its notes say the products "are available at both 4.63 and 9.26 km spatial resolution". Where a record names one thing in two wordings, we keep the more precise one, so we wrote that this dataset's spatial resolution is "4.63 km". We wrote nothing for 9.26 km, which we read as the same data at another resolution: another dataset, with a record of its own. Both readings rest on facts we can't check from the record. We would like to know:

- (a) Is "4km" in such a title the rounded name of the 4.63 km grid, so that the two name one resolution? Our reading, not checked against a source: 4.63 km is about 1/24 of a degree at the equator, and the products are named by the rounded value. More generally: in this catalog, is a title's rounded value always the notes' value, or can the two differ?
- (b) Is the dataset of this record only the 4.63 km one, with the 9.26 km products in a record of their own?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: 4km
- source text: available at both 4.63 and 9.26 km spatial resolution
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution)

### Ground truth schema

- entity class SpatialResolution: an amount of ground each value of the data covers, e.g. 500 m; 4.63 km
- predicate HAS_SPATIAL_RESOLUTION: each of its values covers this much ground, e.g. 500 m

### Options

#### Option 1: Keep the notes' value (as now)

This dataset's spatial resolution is "4.63 km", the more precise wording, and there is no fact for 9.26 km.

#### Option 2: The title's value, when the two differ

"4km" is a resolution of its own, not the rounded 4.63 km: this dataset's spatial resolution is "4km".

### My current reading

Option 1, because we keep the more precise wording, and the record's own words give 4.63 km as one of the two resolutions it is available at. We would move to option 2 only if you say a title's value and the notes' value can name different resolutions.

### My notes

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0". The ground truth triples with HAS_SPATIAL_RESOLUTION so far are listed under Affects: "500m" (the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061"), "4.63 km" (the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0"), and "1 kilometer (km)" (the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid").

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as they were. The expert's (a) now holds the old (a) and the general part of (c); their (b) is the old (b). (a) may be settled from a source too (the Ocean Biology Processing Group's documents on its Level 3 grids).

- The question's opening, as it was: The title of the example below says "4km", and its notes say the products "are available at both 4.63 and 9.26 km spatial resolution". Rule 23 of the annotation guidelines writes one thing with one wording in a record, the more precise one when two wordings name the same thing; its own example is this record: "a title says "4km" and the notes say "4.63 km". Then: "4.63 km", the more precise." So we wrote "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution), and nothing for 9.26 km, which rule 21 leaves out as a fact about another dataset (the same data at another resolution). Whether that is right depends on facts we can't check from the record.
- (b) Is the dataset of this record only the 4.63 km one, with the 9.26 km products in a record of their own, so that 9.26 km is about another dataset?
- (c) The record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" is the same case: its title says "1km" and its notes "produced daily at 1 kilometer (km) pixel resolutions", and we have written "1 kilometer (km)", the wording that spells out its abbreviation. Is a title's rounded or shortened value always the notes' value, for products of this catalog, or can the two differ?
- The question's context, as it was: The spatial resolutions we have written so far: "500m" (the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061"), "4.63 km" (the example below), and "1 kilometer (km)" (the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid").
- The options and reading, as they were: Option 1: The dataset HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution), the more precise wording, and no fact for 9.26 km. Option 2: "4km" is a resolution of its own, not the rounded 4.63 km: the dataset HAS_SPATIAL_RESOLUTION "4km" (SpatialResolution), and rule 23's example changes. My current reading: Option 1, because rule 23 takes the more precise wording and the record's own words give 4.63 km as one of the two resolutions it is available at. We would move to option 2 only if experts say a title's value and the notes' value can name different resolutions.

Withdrawn on 2026-10-26: a question we can settle from sources, so it is no longer asked of the experts; kept whole, so that comments filed under its number still find it.

Checked on 2026-10-26, for (a): PO.DAAC's page for this dataset (https://podaac.jpl.nasa.gov/dataset/MODIS_AQUA_L3_SST_MID-IR_8DAY_4KM_NIGHTTIME_V2019.0) gives "Spatial Resolution: 0.041 Decimal Degrees x 0.041 Decimal Degrees", and its page for the 9km dataset (https://podaac.jpl.nasa.gov/dataset/MODIS_AQUA_L3_SST_MID-IR_8DAY_9KM_NIGHTTIME_V2019.0) "0.083 Decimal Degrees x 0.083 Decimal Degrees": 1/24 and 1/12 of a degree, which at the equator are about 4.6 km and 9.3 km (our arithmetic: about 111.3 km per degree). So the title's "4km" is the rounded name of the 4.63 km grid: checked, for this record. Whether a title's rounded value is always the notes' value, across the catalog: not settled, our reading (it holds for the three records we have, "500m", "4km" and "1km").

Checked on 2026-10-26, for (b): the catalog (020's records.jsonl, 36,406 records, harvested before 2026-10-24) has a record of its own for the 9km products, "MODIS Aqua Level 3 SST MID-IR 8 Day 9km Nighttime V2019.0", beside this one, and the same 4km and 9km pair for Daily, Monthly and Annual. So 9.26 km is about another dataset, as rule 21 reads it. Option 1 stands; the ground truth stays as it is.

### Quoted for us

- Writing a classed triple, rule 21: Another dataset. Include facts about another dataset when the record states a chain of "part of" or "made from" links that connects it to the record's dataset: its parts, what it is part of, what it is made from, and so on through further datasets or variables the record names. Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it. In every case, include the connection the record states (rule 1 of What counts as a fact: only what the record states).
- Writing a classed triple, rule 23: One thing, one wording, within a record. When a record names the same thing more than once, in different words, use the first wording this order picks; the others appear only in an ALSO_KNOWN_AS triple, and only if the record states one (rule 20). 1. The wording that says more: it contains the other's words, each as a whole word, is more precise, or spells out the other's abbreviation.

### Consequences

#### Option 1: Keep the notes' value (as now)

- Nothing changes.
- If "4km" and 4.63 km are one resolution, the ground truth names it the more precise way, and a search by the title's "4km" must know that.

#### Option 2: The title's value, when the two differ

- One ground truth triple changes its object instance, and rule 23's example in the annotation guidelines and in the copy of the rules the [model](../docs/terminology.md#8-the-pipeline) follows changes.
- The notes' "4.63 and 9.26 km" would then describe the products in general, not this dataset.

### Affects

- record at pool position 2: 6cfafd07-40f1-46da-9d92-36c2bb319f0b
- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 18: 0eedd2bc-b2e2-4cc1-a94d-41c141169334
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 2: "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061" (Dataset) HAS_SPATIAL_RESOLUTION "500m" (SpatialResolution)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution)
- classed triple of the record at pool position 6: "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid" (Dataset) HAS_SPATIAL_RESOLUTION "1 kilometer (km)" (SpatialResolution)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_SPATIAL_RESOLUTION "1 kilometer (km)" (SpatialResolution)
- classed triple of the record at pool position 18: "VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002" (Dataset) HAS_SPATIAL_RESOLUTION "30 arc second (1,000 meter)" (SpatialResolution)
- classed triple of the record at pool position 24: "HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH)" (Dataset) HAS_SPATIAL_RESOLUTION "1 degree latitude" (SpatialResolution)
- classed triple of the record at pool position 25: "OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1)" (Dataset) HAS_SPATIAL_RESOLUTION "30 meters" (SpatialResolution)
- ground truth schema entry: entity class SpatialResolution
- ground truth schema entry: predicate HAS_SPATIAL_RESOLUTION
- translation table row: entity class SpatialResolution
- translation table row: predicate HAS_RESOLUTION
- translation table row: predicate HAS_PROPERTY
- rule: Writing a classed triple, rule 21
- rule: Writing a classed triple, rule 23

## Q23: Is flying in the A-train a fact about the spacecraft Aqua, or about its mission?

- status: withdrawn
- priority: low
- question kind: schema entry
- in short: the ground truth schema's SatelliteFormation and FLIES_IN

### The question

The example below says Aqua was launched into its orbit "formation flying in the A-train with other Earth Observation Satellites (EOS)". We wrote that Aqua (a Spacecraft) FLIES_IN the A-train (a SatelliteFormation), both defined below. We would like to know: is "formation flying in the A-train" a fact about Aqua (the spacecraft) or about its mission?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS)
- classed triple: "Aqua" (Platform) FLIES_IN "A-train" (SatelliteFormation)

### Ground truth schema

- entity class SatelliteFormation: a group of spacecraft flying together in formation in orbit, e.g. A-train
- predicate FLIES_IN: flies in formation as part of

### My current reading

A fact about Aqua, the spacecraft, as we wrote it, because it is the spacecraft that flies in the A-train.

### My notes

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", the only tuning record annotated so far that names a group of spacecraft; its one classed triple with FLIES_IN is listed under Affects.

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as they were. The expert's (a) now holds the old (a) and (b); their (b) is the old (c).

- The question's opening, as it was: The example below says Aqua was launched "into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS)". We wrote "Aqua" (Spacecraft) FLIES_IN ("flies in formation as part of") "A-train" (SatelliteFormation), a SatelliteFormation being "a group of Spacecraft flying together in formation in orbit, e.g. the A-train". The A-train may be read in more than one way.
- (b) If it is a constellation: should the ground truth schema's entity class be one for any group of spacecraft that work together (a constellation, a formation, a train), or should formations and constellations be told apart?
- The question's context, as it was: Of the records we have read so far, the example below is the only one that names a group of spacecraft.
- Option 2's words, as they were: An entity class for any group of spacecraft that work together, in place of SatelliteFormation, with a definition that covers formations, constellations and trains, and FLIES_IN read as "is part of this group".

Taken out of the expert's view on 2026-10-26, as a question we can settle from a source; kept here word for word, with the options, my current reading and the consequences, which were about it. The title was "Is the A-train a formation, a constellation, or something else?"; the expert's (b) is now the question, without its letter.

- (a) Is the A-train a formation (spacecraft flying close together, in an arrangement kept on purpose), a constellation (spacecraft in coordinated orbits, which need not fly close together), or something else? Our reading, not checked against a source: NASA also calls it the "Afternoon Constellation". If it is a constellation, does the difference matter to someone searching this catalog, or would one kind of thing for any group of spacecraft that work together do?
- The options, as they were: Option 1: Keep SatelliteFormation as it is. The A-train stays a SatelliteFormation, as the record's own words "formation flying" say. Option 2: One entity class for any group of spacecraft. One kind of thing for any group of spacecraft that work together, in place of SatelliteFormation, covering formations, constellations and trains, and FLIES_IN read as "is part of this group".
- My current reading, as it was: Option 1 for now, because the record itself says "formation flying". We would move to option 2 if you say the A-train is a constellation, or that the difference doesn't matter for a search of this catalog.
- The consequences, as they were: Option 1 (Keep SatelliteFormation as it is): Nothing changes. If the A-train is a constellation, the definition of SatelliteFormation, and its example, say something an expert would not. Option 2 (One entity class for any group of spacecraft): The entity class and predicate are renamed and redefined in the ground truth schema; the one ground truth triple keeps its instances. Groups of spacecraft that other records name are written the same way, whatever their arrangement.

Checked on 2026-10-26: NASA Goddard's fact sheet "Formation Flying: The Afternoon 'A-Train' Satellite Constellation" (FS-2003-1-053-GSFC, March 2003, https://assets.science.nasa.gov/content/dam/science/missions/a-train/publications/A-TrainFactSheet.pdf) says "Since these missions will all fly in tandem, the set of satellites is referred to as a constellation, or alternatively, as a formation", calls "A-Train" "a popular nickname for the Afternoon Constellation", and says the spacecraft keep tight positions ("CALIPSO must not lag Aqua by more than two minutes but may never precede Aqua"). So NASA calls the A-train both, and it does fly in formation, as SatelliteFormation's definition ("a group of Spacecraft flying together in formation in orbit") says: checked. Option 1 stands; the ground truth stays as it is.

Added on 2026-10-31: "Earth Observation Satellites (EOS)" is a name (rule 11 of *Writing a classed triple* keeps it whole), of the group Aqua flies in formation with, so it is a ground truth triple of the same kind as the A-train one: "Aqua" (Spacecraft) FLIES_IN "Earth Observation Satellites (EOS)" (SatelliteFormation), with the same source text. This question's answer applies to both.

Withdrawn on 2026-10-31: settled from the field's practice, so it is no longer asked of the experts; kept whole, so that comments filed under its number still find it. Membership of the A-Train is stated on the spacecraft: Wikidata's item for Aqua (Q17397, "NASA Earth observation satellite") is "part of" the A-Train, and NASA's page for Aqua speaks of the satellite "slowly descending below the A-Train" (https://science.nasa.gov/mission/aqua/), as the GSFC fact sheet checked on 2026-10-26 does. So "Aqua" (Spacecraft) FLIES_IN "A-train" (SatelliteFormation) and FLIES_IN "Earth Observation Satellites (EOS)" (SatelliteFormation) stay, as the current reading has them.

### Quoted for us

- entity class Platform: a craft or station that carries Instruments, in space, in the air, on water or on the ground: a spacecraft, an aircraft, a balloon, a ship or a ground station, e.g. Aqua; Voyager 1

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- classed triple of the record at pool position 4: "Aqua" (Platform) FLIES_IN "A-train" (SatelliteFormation)
- classed triple of the record at pool position 4: "Aqua" (Platform) FLIES_IN "Earth Observation Satellites (EOS)" (SatelliteFormation)
- ground truth schema entry: entity class SatelliteFormation
- ground truth schema entry: predicate FLIES_IN

## Q24: Should facts about a product family be recorded, and as what?

- status: open
- priority: medium
- question kind: records and triples
- in short: rule 21 of the annotation guidelines, and the facts about the other versions, temporal resolutions and spatial resolutions of a product

### The question

A record's notes often describe the family of products its dataset belongs to, not only the dataset itself. The title of the example below says "8 Day 4km Nighttime", so its dataset is the 8-day, 4 km, nighttime product; but its notes begin "Day and night" and say "Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution". Each of those other products is another dataset, with a record of its own, so we leave their facts out of this record: we wrote only that this dataset is weekly (8 day) and 4.63 km, and nothing says the others exist. We would like to know:

- (a) Is the information about the family worth keeping in a knowledge graph of this catalog? Would someone ask "which temporal resolutions does this product come in?", or "is there a 9.26 km version of it?", and expect the answer from a record that describes only one of them?
- (b) If it is, as what? As facts about each of the other products, as facts about a family of products (a group of datasets sharing a name, with the family's own facts), or as facts about the instrument that makes them? And is a fact such as "there is also a daily product" about this dataset (it has siblings), or only about the family?

### Example record

- record id: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- pool position: 4
- title: MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0
- notes: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products from the Moderate-resolution Imaging Spectroradiometer (MODIS) onboard the Aqua satellite. Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution. Aqua was launched by NASA on May 4, 2002, into a sun synchronous, polar orbit with a daylight ascending node at 13:30, formation flying in the A-train with other Earth Observation Satellites (EOS), to study the global dynamics of the Earth atmosphere, land and oceans. MODIS captures data in 36 spectral bands at a variety of spatial resolutions. Two SST products can be present in these files. The first is a skin SST produced for both day and night (NSST) observations, derived from the long wave IR 11 and 12 micron wavelength channels, using a modified nonlinear SST algorithm intended to provide continuity of SST derived from heritage and current NASA sensors. At night, a second SST product is generated using the mid-infrared 3.95 and 4.05 micron wavelength channels which are unique to MODIS; the SST derived from these measurements is identified as SST4. The SST4 product has lower uncertainty, but due to sun glint can only be used at night. To generate the L3 products the L2 pixels are binned into an integerized sinusoidal area grid (ISEAG) and mapped into an equidistant cylindrical (also known as Platte Carre projection. Additional projection detailed can be found at https://oceancolor.gsfc.nasa.gov/docs/format/ The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG) and Peter Minnett and his team at the Rosenstiel School of Marine and Atmospheric Science (RSMAS) are responsible for sea surface temperature algorithm development, error statistics and quality flagging. JPL acquires MODIS ocean L3 SST data from the OBPG and is the official Physical Oceanography Data Archive (PO.DAAC) for SST. The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4
- source text: Day and night spatially gridded (L3) global NASA skin sea surface temperature (SST) products
- source text: Average daily, weekly (8 day), monthly and annual skin SST products
- source text: available at both 4.63 and 9.26 km spatial resolution
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_TEMPORAL_RESOLUTION "weekly (8 day)" (TemporalResolution)
- classed triple: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution)

### Options

#### Option 1: Leave them out, as now

The family's other temporal resolutions, spatial resolutions and times of day are not recorded. A search finds this dataset by its own temporal resolution and spatial resolution only.

#### Option 2: A new entity class for a product family, with its own facts

A family of products (for the example, the MODIS Aqua skin sea surface temperature products) is a thing of its own, with its temporal resolutions, spatial resolutions and times of day as its facts, and the dataset of the record is one of its members.

#### Option 3: Record them on the instrument

The facts are written about the instrument that makes the products, as general facts about it (we already write general facts about a dataset's instrument): MODIS, with the temporal resolutions and spatial resolutions of its skin sea surface temperature products.

#### Option 4: Another way

Please describe it.

### My current reading

Option 1 for now, because our guidelines leave facts of other datasets out, and the family facts would need kinds of things and links our schema doesn't have. But we think the information is worth keeping if you say people ask for it, and we would then lean towards option 2, since the facts are about the family, not about one instrument.

### My notes

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", the densest record we have annotated: the items its notes leave out are listed in `annotations/left_out.md`. Q22 asked a narrower question about the same sentence (is the title's "4km" the notes' "4.63 km"); it was withdrawn on 2026-10-26, settled from PO.DAAC's page for this dataset: "4km" is the rounded 4.63 km grid (see Q22's My notes). Q5 (b) asks what the "Average" means; it is not settled by this one. We decided against merging this into Q19 (releases, "R2019.0" and "Collection"): an answer about whether "R2019.0" is "V2019.0" does not settle whether a family of products is recorded. It is not merged into Q25 either: Q25 asks how the schema groups things; this asks whether the facts are wanted at all, and one answer to this does not settle the other, though option 2 needs Q25's answer for a part-of predicate.

Changed on 2026-10-26, because the review page now shows a record's title only once, in its example: the question said "The example below is titled "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", so its dataset is".

Items of `annotations/left_out.md` that this answer may bring back as ground truth triples:

- the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0": "Day"; "daily", "monthly" and "annual"; "9.26 km"; "Average"; the DOI of the previous v2014.1 datasets;
- the record "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid": the Near Real Time (NRT) product and the product MCD19A1N computed from this dataset, as members of a family (their own question: Q20).

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as they were. The expert's (b) now holds the old (b) and (c).

- The question's opening, as it was: The notes of a record often describe more than the one dataset the record is about: they describe the product family it belongs to. The example below is titled "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", so its dataset is the 8-day, 4 km (4.63 km), nighttime product; its notes say that "Average daily, weekly (8 day), monthly and annual skin SST products at are available at both 4.63 and 9.26 km spatial resolution", and begin "Day and night spatially gridded (L3) ... products". So the record also states which temporal resolutions (daily, monthly, annual), which spatial resolution (9.26 km) and which time of day (day) the other products of the family have. Rule 21 of the annotation guidelines leaves these out, because each of those products is another dataset with a record of its own, where its facts go. The ground truth then says that this dataset is "weekly (8 day)" and "4.63 km", and nothing says that the others exist.
- (b) If it is, as what? As facts about each of the other products (each of them a dataset, but with no record of its own to hold its title), as facts about a family of products (a group of datasets sharing a name, with the family's own facts), or on the instrument that makes them?
- (c) Where a family is named by one record only, as here, is a fact such as "there is also a daily product" about this dataset (it has siblings), or only about the family?
- The question's context, as it was: The same happens with the releases of a product: the record also says "The R2019.0 supersedes the previous v2014.1 datasets which can be found at https://doi.org/10.5067/MODAM-8D4N4", and we wrote only that "V2019.0" replaces "v2014.1", not the address of the older datasets. Another record of the catalog (titled "MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid") names the standard product and its Near Real Time sibling in one sentence. How the groups of datasets could be written, if they are, depends on how the ground truth schema treats kinds and parts of things; that is asked in another question (Q25).
- The example's release passage, taken out of the example: source text "The R2019.0 supersedes the previous v2014.1 datasets"; classed triple "V2019.0" (Version) SUPERSEDES "v2014.1" (Version) (listed under Affects).
- Options 1 and 3, as they were: Option 1: The family's other temporal resolutions, spatial resolutions and times of day are not recorded, by rule 21. A search finds this dataset by its own temporal resolution and spatial resolution only. Option 3: The facts are written about the instrument that makes the products, as general facts about it (rule 21 includes general facts about a dataset's instrument): the instrument "Moderate-resolution Imaging Spectroradiometer (MODIS)" with the temporal resolutions and spatial resolutions of its skin sea surface temperature products.
- My current reading, as it was: Option 1 for now, because rule 21 says so and the family facts need an entity class and predicates the ground truth schema does not have. But we think the information is worth keeping if an expert says people ask for it, and we would then lean towards option 2, since the facts are about the family, not about one instrument. We would like to know first whether a person looking for this product would expect to learn the other temporal resolutions and spatial resolutions from this record.

Checked on 2026-10-31, for the expert's (b): W3C DCAT has a standard home for a product family, dcat:DatasetSeries, "A collection of datasets that are published separately, but share some characteristics that group them", with dcat:inSeries, "A dataset series of which the dataset is part", a kind of dcterms:isPartOf; and it says "As there are no common rules and criteria across domains to decide when dataset series should be created and how they should be organized, DCAT does not prescribe any specific approach" (https://www.w3.org/TR/vocab-dcat-3/). So option 2 has a standard model: a family entity class, and a predicate for membership under PART_OF (Q25). For (a): a study of dataset search found the granularity the user needs among the most requested features (Kacprzak et al., "Characterising dataset search—An analysis of search logs and data requests", *Journal of Web Semantics* 55, 2019; abstract only, strong secondary), which leans towards keeping the family's facts; the answer stays the experts'.

Checked on 2026-10-31, for the expert's (b), in NASA's metadata (it corrects the inventory's "no family field"): UMM-C has a series name, `CollectionCitations.SeriesName`, "The name of the data series, or aggregate data of which the data is a part", and `MetadataAssociations`, whose kinds include Parent and Input, "used to identify a parent metadata record … where a group of metadata records are subsets that can be better represented by one parent metadata record". The tuning products don't use them: MCD19A1N, MCD19A1, MCD19A2N, MYD10_L2 and MOD11A1 have no associations, and only PO.DAAC fills SeriesName, with the title without its version ("MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime"). So they can't serve as a reference now. CMR records no Input association from MCD19A1N to MCD19A2N either.

### Quoted for us

- entity class TemporalResolution: an amount of time between one value of the data and the next, e.g. daily; weekly (8 day)
- predicate HAS_TEMPORAL_RESOLUTION: its values are this far apart in time, e.g. daily
- entity class SpatialResolution: an amount of ground each value of the data covers, e.g. 500 m; 4.63 km
- predicate HAS_SPATIAL_RESOLUTION: each of its values covers this much ground, e.g. 500 m
- predicate SUPERSEDES: replaces this earlier one. A record states this when it says the older one is discontinued or decommissioned and directs users to the newer one
- Writing a classed triple, rule 21: Another dataset. Include facts about another dataset when the record states a chain of "part of" or "made from" links that connects it to the record's dataset: its parts, what it is part of, what it is made from, and so on through further datasets or variables the record names. Leave out facts about other datasets, such as a variant of the record's dataset (the same data at another temporal resolution, spatial resolution, or version), or a product made from it. In every case, include the connection the record states (rule 1 of What counts as a fact: only what the record states).

### Consequences

#### Option 1: Leave them out, as now

- Nothing changes.
- The ground truth never holds a fact of a family, and the model's extracted triples that state one count as wrong.

#### Option 2: A new entity class for a product family, with its own facts

- A new entity class and a predicate saying a dataset is a member of a family (see Q25), in the ground truth schema, with their definitions, and an example in rule 21 of the annotation guidelines and in the model's copy of the rules.
- The listed items become ground truth triples of the family; the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" gets one more ground truth triple, for the membership.
- Every record that lists its siblings is written the same way, so a family has one name in all of them: the work of joining the names of one family grows.

#### Option 3: Record them on the instrument

- The facts are written about MODIS, not about the dataset or its family; they would say that the instrument has "daily" and "monthly" products, which is true of one product of it only, not of all.
- Rule 21's second sentence changes.

#### Option 4: Another way

- Depends on the answer.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 6: 4c64f3ed-39b4-4f95-95a0-022898ba47a4
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_TEMPORAL_RESOLUTION "weekly (8 day)" (TemporalResolution)
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) HAS_SPATIAL_RESOLUTION "4.63 km" (SpatialResolution)
- classed triple of the record at pool position 4: "V2019.0" (Version) SUPERSEDES "v2014.1" (Version)
- rule: Writing a classed triple, rule 21
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

## Q25: Which entity classes are kinds of others, and which groupings of things matter?

- status: open
- priority: medium
- question kind: schema entry
- in short: the ground truth schema as a flat list of entity classes, and its PART_OF predicate

### The question

Our schema is a flat list of kinds of things: none is a kind of another. So a link such as "developed by" has to list Person and Organization one by one, and a search can't ask for "anything that carries instruments". The only link that groups things is PART_OF ("is one part of"). We would like to know:

- (b) Which groupings of things matter, and are they one kind of link? In the example below, the notes name a part of an instrument: "GRaND plus Z boron loaded sensor" is one part of "GRaND". Other groupings of the same shape: a product family (the daily, weekly, monthly and annual products of one kind of data), a mission and its phases, a formation and its spacecraft. For each, is "is part of" the right link, or are they different links (a member of a group, a part of a whole, a phase of a mission) that should not share one?

### Example record

- record id: 99dff022-24ac-48cb-bc83-09fec8b90ad7
- pool position: 5
- title: DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0
- notes: These data are maps of fast neutron residual count rates from the GRaND plus Z boron loaded sensor. The nominal fast neutron count rates were detrended using the GRaND epithermal neutron map to produced this residual map. The residual map is related to the average atomic mass on Vesta. Details of the map and data reduction are described in LAWRENCEETAL2013.
- source text: GRaND plus Z boron loaded sensor
- classed triple: "GRaND plus Z boron loaded sensor" (Instrument) PART_OF "GRaND" (Instrument)

### Ground truth schema

- entity class Organization: a named institution or one of its named parts, not a Mission, e.g. NASA; OBPG

- entity class Person: one named human being, e.g. Peter Minnett
- predicate PART_OF: is one part of

### Options

#### Option 1: Keep the schema flat

No kind of thing is a kind of another, and PART_OF stays for any part of a whole.

#### Option 2: A hierarchy of entity classes, and PART_OF as it is

Kinds of things get broader kinds above them (for example a platform, with spacecraft, aircraft, ship, balloon and ground station under it; an agent, with Person and Organization under it), and PART_OF keeps its one meaning.

#### Option 3: A hierarchy, and separate links for a part, a member and a phase

As option 2, and the groupings of (b) get one link each (part of a whole; member of a group; phase of a mission).

#### Option 4: Another way

Please describe it.

### My current reading

Option 1 for now: the records we have written down so far use PART_OF only for a part of an instrument or of a dataset, and none needs a kind of a kind. We would add the separate links of option 3 only for groupings you say differ.

### My notes

The example is the record "DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0", the only tuning record annotated so far with a PART_OF triple (listed under Affects). Q4 (d) asks the platform half of (1) for the data's carriers; Q24 is the product family half of (2), kept apart because it asks whether the family facts are wanted at all. Both would use the hierarchy this question asks for if it is kept: the improvements item "An entity class hierarchy for the schemas" (`docs/improvements.md`) lists what it touches (the schema reader and its file format, the pin check, step 040's induced schema, the translation table). The same file's item "Kinds of translation, not only "means the same"" would let a row of the translation table say a current-schema entity class is narrower or broader than a ground truth schema one, instead of only equal or none: with a hierarchy, a row for an aircraft could say it is a kind of a platform.

Note on the above: the PART_OF triples listed under Affects now include ones of the records "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" and "Ensemble X-Ray Variability of AGN in 2XMMi-DR3", so "the only tuning record ... with a PART_OF triple" is no longer true; the expert's current reading now says PART_OF is used for a part of an instrument or of a dataset (2026-10-26).

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as they were. The sub-questions (1) and (2) are now the expert's (a) and (b), in plainer words.

- The question's opening, as it was: The ground truth schema is a flat list: no entity class is a kind of another, and no predicate says a thing belongs to a group of things, except PART_OF ("is one part of"), which we coined for one record. Two questions follow.
- (1) Which entity classes are kinds of others? Our guess: a Spacecraft, an aircraft, a ship, a balloon and a ground station are kinds of a platform (the thing that carries instruments; whether this catalog needs one entity class for it is Q4 (d)); a Person, a Team and an Organization are kinds of an agent (a party that develops, sponsors, launches or is responsible for something). If these were kinds of a larger entity class, a predicate such as "developed by" could say "any agent" instead of listing the three, and a search could ask for anything a platform carries. Are these two groups right? Which other kinds of kinds do you see in this catalog (for example, a Dataset and a Document as kinds of something that holds information)?
- (2) Which groupings of instances matter? In the example below, the notes name a part of an instrument: "GRaND plus Z boron loaded sensor" is one part of "GRaND". Other groupings of the same shape: a product family (the daily, weekly, monthly and annual products of one kind of data, Q24), a mission and its phases, a formation and its spacecraft. For each, is "is part of" the right link, or are they different kinds of link (a member of a group, a part of a whole, a phase of a mission) that should not share one predicate?
- The question's context, as it was: Today each predicate lists the entity classes it takes, so "developed by" lists Organization, Person and Team one by one. A hierarchy (an entity class that is a kind of another) is standard in schemas of knowledge graphs; adding one to the ground truth schema would change how the ground truth is written and how the model's schema is compared with it, so we want to know first whether the catalog needs it.
- The options and reading, as they were: Option 1: No entity class is a kind of another, and PART_OF stays for any part of a whole. Option 2: Entity classes get kinds (for example a platform with Spacecraft, aircraft, ship, balloon and ground station under it; an agent with Person, Team and Organization under it), and PART_OF keeps its one meaning. Option 3: As option 2, and the groupings of question (2) get one predicate each (part of a whole; member of a group; phase of a mission). My current reading: Option 1 for now: the ground truth has one use of PART_OF and no record whose facts need a kind of a kind. We would move to option 2 if experts say the two groups of question (1) are right, since the same fact is then asked across several entity classes, and we would add the separate links of option 3 only for groupings that experts say differ.

Taken out of the expert's view on 2026-10-31, as settled from the field's practice (the research of 2026-10-31); kept here word for word: "- (a) Which kinds of things are kinds of others? Our guess: a spacecraft, an aircraft, a ship, a balloon and a ground station are kinds of a platform (the thing that carries instruments); a Person and an Organization (defined below) are kinds of an agent (a party that develops, sponsors, launches or is responsible for something). Are these two groups right? Which others do you see in this catalog (for example, a dataset and a document as kinds of something that holds information)?" My current reading, as it was: "Option 1 for now: the records we have written down so far use PART_OF only for a part of an instrument or of a dataset, and none needs a kind of a kind. We would move to option 2 if you say the two groups of (a) are right, and add the separate links of option 3 only for groupings you say differ."

Checked on 2026-10-31, the old (a): the two groups are the field's own. W3C PROV-O has an agent, "something that bears some form of responsibility for an activity taking place, for the existence of an entity [a thing], or for another agent's activity", with prov:Person and prov:Organization as kinds of it (https://www.w3.org/TR/prov-o/); W3C SOSA a platform, "an entity [a thing] that hosts other entities [things], particularly Sensors, Actuators, Samplers, and other Platforms" (https://www.w3.org/TR/vocab-ssn/); NASA's GCMD groups its platforms as space-, air-, water- and land-based. No standard I checked puts a dataset and a document under one class. Whether our schema gets the hierarchy (option 2) is ours to decide after the first run: docs/improvements.md, *An entity class hierarchy for the schemas*.

Checked on 2026-10-31, for the expert's (b): the standards have one general part-of with narrower links under it. In the OBO ontologies' list of links (RO), member_of (RO_0002350) is a sub-property of part_of (BFO_0000050), which is transitive (http://purl.obolibrary.org/obo/ro/core.owl); DCAT's dcat:inSeries is a sub-property of dcterms:isPartOf; W3C ORG keeps org:unitOf and org:memberOf apart. Winston, Chaffin and Herrmann, "A Taxonomy of Part-Whole Relations", in *Cognitive Science* 11, 1987, list six kinds of part-whole link and find that "intransitivities arise due to equivocations between different types of semantic relations [links]". So keeping PART_OF alone is compatible with the standards (each narrower link is a kind of it); separate links matter once the graph chains part-of links, and option 3 would make them sub-predicates of PART_OF, so that translation and pairing still meet at PART_OF.

### Quoted for us

- entity class Instrument: a device that takes measurements
- entity class Platform: a craft or station that carries Instruments, in space, in the air, on water or on the ground: a spacecraft, an aircraft, a balloon, a ship or a ground station, e.g. Aqua; Voyager 1

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
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- record at pool position 16: ec41fd5d-1159-4aa8-9803-5346e2324a20
- record at pool position 19: 6f63dd10-376e-4d17-9156-f2155637e74d
- record at pool position 24: 77a0cb5f-7d69-4f13-aeb1-ce1378d7f1a9
- record at pool position 25: ed2cea26-ed6c-4138-be69-3d32d4ce4858
- classed triple of the record at pool position 5: "GRaND plus Z boron loaded sensor" (Instrument) PART_OF "GRaND" (Instrument)
- classed triple of the record at pool position 9: "encounter data" (Dataset) PART_OF "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset)
- classed triple of the record at pool position 9: "RDR data" (Dataset) PART_OF "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset)
- classed triple of the record at pool position 9: "EDR (raw) sensor data" (Dataset) PART_OF "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" (Dataset)
- classed triple of the record at pool position 12: "table1.dat" (Dataset) PART_OF "CDS Catalog J/A+A/536/A84" (Dataset)
- classed triple of the record at pool position 16: "PWS spectrum analyzer" (Instrument) PART_OF "Plasma Wave Spectrometer (PWS)" (Instrument)
- classed triple of the record at pool position 19: "BARREL" (Mission) PART_OF "NASA Living with a Star" (Organization)
- classed triple of the record at pool position 19: "2013 balloon campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "2014 balloon campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "August 2015 BARREL campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 19: "2016 campaign" (Campaign) PART_OF "BARREL" (Mission)
- classed triple of the record at pool position 24: "mean" (Variable) PART_OF "Geopotential Height Zonal Fourier Coefficients" (Variable)
- classed triple of the record at pool position 25: "Satellite Needs Working Group (SNWG)" (Organization) PART_OF "U.S. Government" (Organization)
- ground truth schema entry: predicate PART_OF
- translation table row: predicate PART_OF
- translation table row: predicate CONTAINS
- pipeline method: docs/improvements.md: An entity class hierarchy for the schemas
- pipeline method: docs/improvements.md: Judgements are Equivalent, Narrower, Broader, or Unrelated

## Q26: Should a study's aim, method and findings, as a record tells them, be facts of the knowledge graph?

- status: withdrawn
- priority: medium
- question kind: records and triples
- in short: records that tell the study a table comes from; a study's aim, method and findings

### The question

Some records of the catalog describe a table from an astronomical study, and most of their notes tell the study itself: what the authors aimed to find, the method they used, and what they found. The example below is one: a table of quasars observed by XMM-Newton. We have written down what the table holds and where it comes from, and left the study's aim, method and findings out for now. We would like to know:

- (a) For someone searching this catalog, are a study's findings (for example "a strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF") worth having in the knowledge graph, or only what the table holds and where it comes from?
- (b) If they are, whose facts are they: "the authors" (the notes' own words), the table itself (whose title names what the study is about), or the publication the table comes from (which the record names only by its catalog's key, "CDS Catalog J/A+A/536/A84")?

### Example record

- record id: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- pool position: 12
- title: Ensemble X-Ray Variability of AGN in 2XMMi-DR3
- notes: The X-ray variability of active galactic nuclei (AGN) has been most often investigated with studies of individual, nearby sources, and only a few ensemble analyses have been applied to large samples in wide ranges of luminosity and redshift. In their study, the authors aimed to determine the ensemble variability properties of two serendipitously selected AGN samples extracted from the catalogs of XMM-Newton and Swift (the latter is not included in this table, notice), with redshift between ~ 0.2 and ~ 4.5, and X-ray luminosities, in the 0.5 - 4.5 keV band, between ~ 10^43 erg/s and ~ 10^46 erg/s. They used the structure function (SF), which operates in the time domain, and allows for an ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived. The SF is also more appropriate than fractional variability and excess variance, because these parameters are biased by the duration of the monitoring time interval in the rest-frame, and therefore by cosmological time dilation. The authors find statistically consistent results for the two samples, with the SF described by a power law of the time lag tau, approximately as SF ~ tau^0.1. They do not find evidence of the break in the SF, at variance with the case of lower luminosity AGNs. They confirm a strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF. They also find evidence in support of a weak, intrinsic, average increase of X-ray variability with redshift. For XMM, the authors used the version of the Serendipitous Source Catalog then available, namely 2XMMi-DR3, the latest incremental update of the second version of the catalogue, with observations made between 2000 February 3 and 2008 October 08; all datasets were publicly available by 2009 October 31, but not all public observations are included in this catalog. The total area of the catalog fields is ~ 814 deg^2, but taking account of the substantial overlaps between observations, the net sky area covered independently is ~ 504 deg^2. The 2XMMi-DR3 catalogue contains 353,191 detections (above the processing likelihood threshold of 6), related to 262,902 unique X-ray sources, therefore a significant number of sources (41,979) have more than one record within the catalog. The selected sources were cross-correlated with the DR7 edition of the SDSS Quasar Catalog (Schneider et al. 2010, AJ, 139, 2360) to obtain redshifts and spectral classifications for the sources. The authors used a maximum distance of 1.5 arcseconds, corresponding to the uncertainty in the X-ray positions, resulting in 412 quasars that were observed by XMM-Newton from 2 to 25 epochs each for a total of 1376 observations. The authors refer to these sources as the XMM-Newton sample. This table was created by the HEASARC in April 2012 based on CDS Catalog J/A+A/536/A84 [https://cdsarc.cds.unistra.fr/ftp/cats/J/A+A/536/A84] file table1.dat. This is a service provided by NASA HEASARC .
- source text: In their study, the authors aimed to determine the ensemble variability properties of two serendipitously selected AGN samples
- source text: They used the structure function (SF)
- source text: The authors find statistically consistent results for the two samples
- source text: The authors find statistically consistent results for the two samples, with the SF described by a power law of the time lag tau, approximately as SF ~ tau^0.1
- source text: They confirm a strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF
- source text: They also find evidence in support of a weak, intrinsic, average increase of X-ray variability with redshift

### Options

#### Option 1: Add them, with the authors as their subject

The study's aim, method and findings become facts, each about "the authors".

#### Option 2: Add them, with the table as their subject

The same facts, each about the table: the table's aim is the study's aim, and the findings are the table's.

#### Option 3: Leave the study out

Only what the table holds, how it was made and where it comes from are facts; the study's aim, method and findings stay left out, as now.

### My current reading

Option 3 for now: we keep what the table holds and where it comes from, and the study's aim, method and findings wait for your answer. If your answer to (a) is that findings belong in the knowledge graph, option 1 or 2, by your answer to (b).

### My notes

The example is the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3", the only tuning record annotated so far that tells a study (decided 2026-10-25, for us to confirm; settled on 2026-10-31, below, when this question was withdrawn). Its other doubts: the source catalogs as datasets, and AGN as a target (Q12 (d)); the authors' aim and the method's "allows for" as purposes (Q9 (d)). What was left out, with its rule, is in `annotations/left_out.md`.

Three more items of `annotations/left_out.md` for this record wait on this answer (decided 2026-10-25): "serendipitously selected" (how the study selected its samples), written with the study's method if the answer is option 1 or 2, else left out; "corresponding to the uncertainty in the X-ray positions" (why the maximum distance of 1.5 arcseconds was chosen), written with the pending fact HAS_MATCHING_DISTANCE if that fact is written, else left out; "taking account of the substantial overlaps between observations" (how the net sky area of 2XMMi-DR3, our ground truth triple HAS_SKY_AREA "~ 504 deg^2", was computed from its fields), which is a method of the catalog, not of the study, so it is written only if the answer makes such methods facts too. On 2026-10-30 the ground truth schema's Team ("a group of people without a name of its own, e.g. Peter Minnett and his team") was removed: a named group is an Organization, and an unnamed group gives no fact (What counts as a fact, rule 9). "The authors" names no specific group, so option 1 as worded ("the authors" as the subject) would need a named subject or a decision to bring Team back; the pending facts below keep "(Team)" as they were written on 2026-10-25.

Pending facts, for the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (bb1fe4b0, in the ground truth now without them; decided 2026-10-25, for us to confirm; settled on 2026-10-31, below: the aim and the method are written, the facts with "the authors" as their subject are not), each added if the answer says yes:

- pending fact: "the authors" (Team) HAS_PURPOSE "determine the ensemble variability properties of two serendipitously selected AGN samples" (Purpose)
- pending fact: "the authors" (Team) USED_METHOD "structure function (SF)" (Algorithm)
- pending fact: "structure function (SF)" (Algorithm) HAS_PURPOSE "ensemble analysis even when only a few observations are available for individual sources and the power spectral density (PSD) cannot be derived" (Purpose)
- pending fact: "the authors" (Team) REPORTED "statistically consistent results for the two samples" (Finding)
- pending fact: "the authors" (Team) REPORTED "SF described by a power law of the time lag tau, approximately as SF ~ tau^0.1" (Finding)
- pending fact: "the authors" (Team) REPORTED "strong anti-correlation of the variability with X-ray luminosity, accompanied by a change of the slope of the SF" (Finding)
- pending fact: "the authors" (Team) REPORTED "evidence in support of a weak, intrinsic, average increase of X-ray variability with redshift" (Finding)
- pending fact: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) DEVELOPED_BY_PARTY "the authors" (Team), since the record says what they selected and how
- pending fact: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_MATCHING_DISTANCE "1.5 arcseconds" (Value), a detail of the study's method, with a predicate to coin

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as they were. Sub-question (c) is ours to settle once (a) and (b) are answered (our guidelines already leave out uncertain facts, and a finding about a sample not in the table is a fact about another dataset).

- The question's opening, as it was: Some records of the catalog describe a table from an astronomical study, and most of their notes tell the study itself: what the authors aimed to find, the method they used, and what they found. The example below is one. We have left all of it out of the ground truth for now. If it is to be written, we would write it with "the authors" as the subject (a Team, the ground truth schema's entity class for "a group of people without a name of its own"), and we would coin three entries: the predicates USED_METHOD and REPORTED, and the entity class Finding.
- (b) If they are: is "the authors" the right subject, or the table itself (whose title names what the study is about), or the publication the table comes from (which the record names only by its catalog's key, "CDS Catalog J/A+A/536/A84")?
- (c) Some findings are about both samples of the study, one of which is not in this table ("the latter is not included in this table"), and one is hedged ("evidence in support of"). Should those be written too, and as what?
- The question's context, as it was: The notes also say what is in the table: its sources were selected from "2XMMi-DR3", "cross-correlated with the DR7 edition of the SDSS Quasar Catalog", "resulting in 412 quasars that were observed by XMM-Newton from 2 to 25 epochs each for a total of 1376 observations". Those we wrote as facts of the table, whatever the answer here. One finding is negated ("They do not find evidence of the break in the SF"), and we wrote no fact for it, since the annotation guidelines leave out negated facts. We also left out the background the notes start with (how the X-ray variability of AGN "has been most often investigated"), and that the structure function "is also more appropriate than fractional variability and excess variance": the first names no study or thing of its own, and the second is a judgement.
- Options 1 and 2, as they were: Option 1: The study's aim, method and findings become facts, each with "the authors" as its subject. Option 2: The same facts added, with the table's title as their subject: the table HAS_PURPOSE the study's aim, and the findings are the table's.
- My current reading, as it was: Option 3 for now (decided 2026-10-25, for us to confirm): the ground truth keeps what the table holds and where it comes from, and the study's aim, method and findings wait for your answer. If your answer to (a) is that findings belong in the knowledge graph, option 1 or 2, by your answer to (b).

Withdrawn on 2026-10-31: settled by me, so it is no longer asked of the experts; kept whole, so that comments filed under its number still find it. Decided: the study's aim and method are facts of the record's dataset, written with the record's words: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_PURPOSE "determine the ensemble variability properties of two serendipitously selected samples" (Purpose) (rules 19, 22 and 23 of *Writing a classed triple*: rule 19 takes "AGN" out, a target body, already the ground truth triple HAS_TARGET "active galactic nuclei (AGN)"; "serendipitously selected" names no method, so it stays in the instance, by rule 24's *Words that name no method*), and "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) PRODUCED_USING_ALGORITHM "structure function (SF)" (Algorithm) (rule 24). Its findings, and its background, are left out by a new part of rule 8 of *What counts as a fact*, *A study a record tells*. Why: the knowledge graph is for finding the catalog's datasets; schema.org's Dataset has `measurementTechnique` (how the data were made) but nothing for findings, and W3C DCAT has neither; research knowledge graphs such as the Open Research Knowledge Graph do store findings, for another purpose: comparing papers. The method's details: "serendipitously selected" stays in the purpose (above); "cross-correlated" names no method (rule 24), as before; the maximum distance of 1.5 arcseconds is a setting of the matching step, and "corresponding to the uncertainty in the X-ray positions" is why it was chosen, both left out by rule 24 (a step gives up to two ground truth triples); what the structure function "allows for" waits on Q9 (b), with its would-be ground truth triple in annotations/pending_triples.csv; "which operates in the time domain" waits on Q28 (d); what the record says about the two measures the study did not use is left out by rule 8's new part. The pending facts above with "the authors" (Team) as their subject are not written: "the authors" names no specific group (rule 9).

### Quoted for us


- entity class Purpose: an aim something is meant to achieve
- entity class Algorithm: a method applied to data to compute a result, e.g. series of screens; modified nonlinear SST algorithm
- predicate HAS_PURPOSE: is meant to achieve
- What counts as a fact, rule 2: Every fact the record states, unless a rule leaves it out: rule 1 above and rules 3 to 10 below, and rules 16, 20, 21 and 24 of Writing a classed triple, or it waits on an expert's answer (annotations/questions_for_experts.md). This holds whether or not the ground truth schema has an entity class or predicate for it.
- What counts as a fact, rule 6: Not negated facts.
- What counts as a fact, rule 7: Not facts the record doesn't assert as true: uncertain ones, and ones it requires, requests or recommends.
- Writing a classed triple, rule 12: The subject instance is what the sentence is about, which isn't always the title.

### Consequences

#### Option 1: Add them, with the authors as their subject

- The pending facts are added, with the three entries (the predicates USED_METHOD and REPORTED, the entity class Finding) coined in the ground truth schema.
- The [model](../docs/terminology.md#8-the-pipeline) must write a study's findings the same way, or step 070 counts them as missed.

#### Option 2: Add them, with the table as their subject

- The pending facts are added with the table's title as their subject instead of "the authors" (the DEVELOPED_BY_PARTY "the authors" one is then not needed), with the same three entries coined.

#### Option 3: Leave the study out

- Nothing changes in the ground truth: the pending facts and their coined entries are already out (2026-10-25).
- The annotation guidelines get a rule that leaves a study's findings out, and so does the model's copy of the rules (`common/common_prompts/extraction_rules.txt`).

### Affects

- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) HAS_PURPOSE "determine the ensemble variability properties of two serendipitously selected samples" (Purpose)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) PRODUCED_USING_ALGORITHM "structure function (SF)" (Algorithm)
- rule: What counts as a fact, rule 2
- rule: Writing a classed triple, rule 12
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

## Q27: Words that say how a fact holds: do people searching need them?

- status: withdrawn
- priority: medium
- question kind: rule
- in short: words such as "collaboratively", "entire", "prime" and "associated", and a possible new rule of *What counts as a fact* in the annotation guidelines

### The question

Some words of a record only say how a fact holds: we have written the fact down, and the word adds only how it holds. We have left these words out for now. The four we have found so far:

| Record | The record's words | The fact we wrote down | What the word adds |
|---|---|---|---|
| the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005" | "developed collaboratively between the U.S. National Aeronautics and Space Administration (NASA) and Argentina's space agency, Comisión Nacional de Actividades Espaciales (CONAE)" | the mission was developed by NASA, and by CONAE | "collaboratively": how the two agencies worked |
| the record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" | "The RDR data convert the EDR (raw) sensor data, from the entire comet encounter" | the RDR data were collected during the encounter | "entire": how much of the encounter the raw (EDR) data come from |
| the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" | "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)" | the dataset is about the comet | "prime": that the comet is the main target |
| the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" | "Provided along with the daytime and nighttime surface temperature bands are associated quality control assessments" | the dataset holds quality control assessments | "associated": that the assessments go with the temperatures |

We would like to know:

- (a) For each word in the table: would someone searching this catalog want to find datasets by it, or can it be left out? "prime" in particular: would someone care whether a body is a dataset's main target, rather than one of its targets? Our reading, not checked against a source: a main target means that other bodies may be in the images too.

### Options

#### Option 1: Leave them out, by a new rule

A new rule for what we write down: "Not a word that only says how a fact holds. A ground truth triple has no place for it: the subject and object are things, and the predicate is the link." What we have written stays as it is now.

#### Option 2: Keep the ones people search on

Each word that people search on gets a fact of its own (for example, a link for a dataset's main target); the other words are left out by the rule of option 1.

### My current reading

Option 1, because in each case the fact we wrote already finds the dataset, and the word adds nothing a search would use. "prime" is the one we are least sure of, since a search for the other bodies in the images would need it.

### My notes

The example is the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0". The four words are left out now, each an item of `annotations/left_out.md` that waits on this answer (decided 2026-10-25): "collaboratively" (the record "Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005"), "entire" (the record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0"), "prime" (the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0") and "associated" (the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006").

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as they were. The table already shows each record's words, so the example record ("prime") is out of the expert's view, and the table's facts are said in plain words. The old (b) is now part of (a); the old (c), the wording of the new rule, is ours to settle once (a) is answered (option 1 quotes it).

- The question's opening, as it was: Some words of a record say how a fact holds: the ground truth triple already states the fact, and the word adds only how it holds. We have left these words out of the ground truth for now.
- The table's third column, as it was, row by row: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization), and the same with "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization); "RDR data" (Dataset) HAS_MISSION_PHASE "encounter" (MissionPhase); "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_TARGET "67P/Churyumov-Gerasimenko 1 (1969 R1)" (CelestialBody); "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_MEASUREMENTS_OF "quality control assessments" (PhysicalQuantity). The second row's last column was: "entire": how much of the phase the data come from.
- (a) For each word in the table: would someone searching this catalog want to find datasets by it, or can it be left out?
- (b) "prime" in particular: would someone searching care whether a body is a dataset's main target, rather than one of its targets? Our reading, not checked against a source: a main target means that other bodies may be in the images too.
- (c) If such words can be left out in general, is this new rule right: "Not a word that only says how a fact holds. A ground truth triple has no place for it: the subject and object are things, and the predicate is the link."
- The example record, as it was: the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (ab33f184-95f4-4f33-8f3d-c4a09ec525d3), source text "The prime target is comet 67P/Churyumov-Gerasimenko 1 (1969 R1)", classed triple "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_TARGET "67P/Churyumov-Gerasimenko 1 (1969 R1)" (CelestialBody).
- The options and reading, as they were: Option 1: A new rule of *What counts as a fact*: "Not a word that only says how a fact holds. A ground truth triple has no place for it: the subject and object are things, and the predicate is the link." The ground truth stays as it is now. Option 2: Each word that people search on gets a ground truth triple of its own, with a predicate coined for it (for example, a predicate for a dataset's main target); the other words are left out by the rule of option 1. My current reading: Option 1, because in each case the ground truth triple already finds the dataset, and the word adds nothing a search would use. "prime" is the one we are least sure of, since a search for the other bodies in the images would need it.

Withdrawn on 2026-10-31: settled by me, so it is no longer asked of the experts; kept whole, so that comments filed under its number still find it. Decided: option 1, as a sentence of rule 9 of *What counts as a fact* (not a new rule, so that no rule is renumbered): "A word that only says how another fact holds gives no ground truth triple, and is not part of an instance: its subject would be that fact, not a thing the record names." Rule 11's exceptions now name rule 9 too, and the model's copy of the rules says the same. Why: saying how a fact holds needs a fact about a fact, a qualifier kept with the ground truth triple it holds for (as Wikidata's statement qualifiers do), which is future work (docs/improvements.md, *Rule 19 can lose which fact a qualifier went with*, option 4). The four items of annotations/left_out.md now cite that sentence.

Corrected on 2026-10-31 (the research of that day): the table's second row said, word for word: "| the record "STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0" | "The RDR data convert the EDR (raw) sensor data, from the entire comet encounter" | the RDR data were collected during the encounter | "entire": how much of the encounter the data come from |" "entire" fits the EDR (raw) data, not the RDR data: the RDR data cover the encounter "up to before the start of the anomaly" (the data set's catalog file; Q5's My notes). The fact we wrote stays true, since the RDR data come only from the encounter.

### Quoted for us

- entity class CelestialBody: a natural object in space, or a kind of such objects, e.g. Vesta; active galactic nuclei
- predicate HAS_TARGET: is about, or studies, this CelestialBody
- predicate DEVELOPED_BY_PARTY: was built or created by this Person or Organization
- predicate HAS_MISSION_PHASE: was collected during this MissionPhase
- predicate HAS_MEASUREMENTS_OF: holds measurements of this PhysicalQuantity
- What counts as a fact, rule 2: Every fact the record states, unless a rule leaves it out: rule 1 above and rules 3 to 10 below, and rules 16, 20, 21 and 24 of Writing a classed triple, or it waits on an expert's answer (annotations/questions_for_experts.md). This holds whether or not the ground truth schema has an entity class or predicate for it.

### Consequences

#### Option 1: Leave them out, by a new rule

- The annotation guidelines get the new rule in *What counts as a fact*, and the model's copy of the rules (`common/common_prompts/extraction_rules.txt`) gets the same.
- The ground truth doesn't change; the four items of `annotations/left_out.md` get the new rule as their reason.

#### Option 2: Keep the ones people search on

- New predicates in the ground truth schema for the words that matter (for example, a predicate for a dataset's main target), with a rule or an example for them in the annotation guidelines and in the model's copy of the rules.
- The words that matter come back from `annotations/left_out.md` as ground truth triples; the others get the rule of option 1 as their reason.

### Affects

- record at pool position 3: 2705e0d1-95e7-4588-813b-ca91a6da94ff
- record at pool position 9: dc4ff01b-12f0-4235-8c8a-afb4bfb3bdbb
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "National Aeronautics and Space Administration (NASA)" (Organization)
- classed triple of the record at pool position 3: "Aquarius/Satélite de Aplicaciones Científicas (SAC-D)" (Mission) DEVELOPED_BY_PARTY "Comisión Nacional de Actividades Espaciales (CONAE)" (Organization)
- classed triple of the record at pool position 9: "RDR data" (Dataset) HAS_MISSION_PHASE "encounter" (MissionPhase)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) HAS_TARGET "67P/Churyumov-Gerasimenko 1 (1969 R1)" (CelestialBody)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) HAS_ANCILLARY_DATA "quality control assessments" (Variable)
- rule: What counts as a fact, rule 2
- pipeline method: annotations/ground_truth_schema.txt: a new predicate for each word found worth one (option 2)
- pipeline method: common/common_prompts/extraction_rules.txt: the model's copy of the annotation guidelines' rules, which changes with a rule

## Q28: Facts we have no predicate for yet: is each worth a fact?

- status: withdrawn
- priority: low
- question kind: records and triples
- in short: words that state something no predicate of the ground truth schema holds: "which operates in the time domain" (once "NASA", "known issues" and "Lien", settled on 2026-10-31)

### The question

Some words of a record state something that none of the links in our schema can hold. We have left them out for now. The one we have found so far: the record "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" says the method its study used, "the structure function (SF), which operates in the time domain". We wrote down that the dataset was made with the structure function; no link of our schema says in which domain a method works. We would like to know:

- (d) Is "which operates in the time domain" worth a fact of its own about the method (in which domain it works), for someone searching this catalog?

### My current reading

Leave it out for now: a search for datasets made with a time-domain method seems rare, and the method's name already finds them. We would write a fact if you say people search by it.

### My notes

Checked against sources on 2026-10-30: PDS defines a lien as "A formally expressed issue with one or more products in a collection", and ESA's procedure for this review says "Within ESA, issues raised are known as RIDs (Review Item Discrepancies), while PDS refer to these as liens" (https://sbnreview.astro.umd.edu/201909_Rosetta/procedure_docs/RO-SGS-PR-1023-App5%20-%20RSI%20Rosetta%20CLS%20Science%20Archive%20Review.pdf). The current reading holds: "Lien" names no particular issue.

The example is the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0". Each of the three is an item of `annotations/left_out.md` that waits on this answer (decided 2026-10-25), and each answer settles one item: if it is worth a fact, a predicate is coined for it in the ground truth schema and the item comes back as a ground truth triple; if not, it stays left out. (a) is about the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0", (b) about the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006", (c) about the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0".

Taken out of the expert's view on 2026-10-26, so that the question can be read in a minute or two; kept here as they were. The table already shows each record's words, so the example record is out of the expert's view, and the table's facts are said in plain words. The sub-questions are the same three.

- The question's opening, as it was: Some words of a record state something that no predicate of the ground truth schema holds, beyond a ground truth triple we wrote from the same passage or about the same thing. We have left them out of the ground truth for now.
- The table's third column, as it was, row by row: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" (Organization), from "The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)"; "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) DOCUMENTED_AT "https://landweb.modaps.eosdis.nasa.gov/knownissue?sensor=MODIS&sat=Terra&as=6" (WebPage); "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) REVISED_AFTER "September 2019 PSA/PDS external peer review" (Task).
- (a), (b), as they were: (a) Is "NASA" in "global NASA skin sea surface temperature (SST) products" a fact beyond who generated the products, worth a predicate of its own (whose products they are)? (b) Should the ground truth say what a web page is about (here, known issues), beyond that more details are written there?
- The example record, as it was: the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (03a09af3-081e-4db6-9e3b-ea7c0e3138bd), source texts "global NASA skin sea surface temperature (SST) products" and "The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)", classed triple "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" (Organization).
- My current reading, as it was: Leave all three out, as now. For (a), the ground truth triple of who generated the products already says they are NASA's. For (b) and (c), we would write a fact if people search for a dataset's known issues, or for what a review changed.

Taken out of the expert's view on 2026-10-31, as a question we can settle from sources; kept here word for word. The (c) was: "(c) What does "Lien" mean here, and is it worth a fact beyond that the dataset was corrected after the review? Our reading, not checked against a source: it names the issues the review raised." The sources checked on 2026-10-30 (above) answer its first half: PDS's glossary, in its *PDS4 Mission Proposer's Archive Guide* (2019, https://pds.nasa.gov/home/proposers/Mission-Proposers-Archive-Guide-v5_clean_20190424.pdf), defines "lien: A formally expressed issue with one or more products in a collection"; "All recorded liens must be resolved before the data are incorporated into the PDS archive" (*The Peer Review Process*, https://pds.nasa.gov/datastandards/training/documents/Peer%20Review%20Process.pdf); and ESA's procedure for this very review says "PDS refer to these as liens". So "Lien corrected" means corrected to resolve the issues the reviewers raised, as our reading said; the expert's (c) now gives that meaning and asks only whether it is worth a fact.

Taken out of the expert's view on 2026-10-31, as settled by me; kept here word for word. The question was:

Some words of a record state something that none of the links in our schema can hold, beyond a fact we already wrote down from the same passage. We have left them out for now. The three we have found so far:

| Record | The record's words | The fact we wrote down | What is left out |
|---|---|---|---|
| the record "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" | "global NASA skin sea surface temperature (SST) products", and later "The NASA MODIS L3 SST data products are generated by the NASA Ocean Biology Processing Group (OBPG)" | the dataset was made by the NASA Ocean Biology Processing Group (OBPG) | "NASA": whose products these are |
| the record "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" | "For complete information about known issues please refer to the MODIS/VIIRS Land Quality Assessment website" | more details about the dataset are at that website's address | what the page is about: known issues |
| the record "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" | "Lien corrected dataset after September 2019 PSA/PDS external peer review" | the dataset was corrected after the September 2019 PSA/PDS external peer review | "Lien": what was corrected |

We would like to know:

- (a) Is "NASA" in "global NASA skin sea surface temperature (SST) products" a fact beyond who generated the products, worth a link of its own (whose products they are)?
- (b) Should we say what a web page is about (here, known issues), beyond that more details are written there?
- (c) Is "Lien" worth a fact beyond that the dataset was corrected after the review? (In the Planetary Data System's peer reviews, a lien is "A formally expressed issue with one or more products in a collection": here, the issues the review raised.)

Decided on 2026-10-31: (a) "NASA" is left out by rule 16 of *Writing a classed triple*: by rule 19's *Whose fact it is*, it qualifies the products, the record's dataset, so its fact would be who made them, which the ground truth triple DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" states more precisely (rule 23); (b) "known issues" is left out by rule 9's new sentence ("A word that only says how another fact holds gives no ground truth triple"): it says what the page's details are about, how DOCUMENTED_AT holds, and the field's own predicates (W3C DCAT's `dcat:landingPage`, FOAF's `foaf:page`, "A page or document about this thing") say no more than DOCUMENTED_AT does; DOCUMENTED_AT is now pinned to its objects, "more details about it are written at this WebPage or in this Document"; (c) "Lien" is left out by rule 16: REVISED_AFTER already says the dataset was corrected after the review, and a lien is an issue the review raised (PDS's definition, above). The expert's (d) is new, from the decision on Q26 of the same day. My current reading, as it was before 2026-10-31: "Leave all three out, as now. For (a), the fact of who generated the products already says they are NASA's. For (b) and (c), we would write a fact if people search for a dataset's known issues, or for what a review changed."

Withdrawn on 2026-10-31: settled by me, so it is no longer asked of the experts; kept whole, so that comments filed under its number still find it. (d) is a final left-out, by rule 8 of *What counts as a fact*, *A study a record tells* ("the study's aim and its method are facts of the record's dataset … The rest of the study is not"): the method is a ground truth triple already, "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) PRODUCED_USING_ALGORITHM "structure function (SF)" (Algorithm), and in which domain it works is a detail the study gives of its method. The words are the authors' own abstract (the CDS ReadMe of J/A+A/536/A84 repeats them). The field does classify methods this way: the Unified Astronomy Thesaurus, which the AAS journals and ADS use for subject keywords, has "Time domain astronomy" (http://astrothesaurus.org/uat/2109) under "Astronomical methods", and "Time series analysis" among its astrostatistics techniques (https://github.com/astrothesaurus/UAT). So a link from "structure function (SF)" to that list goes to docs/improvements.md, *Knowledge enrichment from the model, verified and labelled* (080), not to the ground truth.

### Quoted for us

- entity class Organization: a named institution or one of its named parts, not a Mission, e.g. NASA; OBPG
- predicate DEVELOPED_BY_PARTY: was built or created by this Person or Organization
- entity class WebPage: a web address, written as the address itself, other than a DOI written as an address (an Identifier), e.g. https://oceancolor.gsfc.nasa.gov/docs/format/
- predicate DOCUMENTED_AT: more details about it are written at this WebPage or in this Document
- entity class Task: a piece of work a Person or Organization does or is in charge of, e.g. quality flagging
- predicate REVISED_AFTER: was corrected after this review
- What counts as a fact, rule 2: Every fact the record states, unless a rule leaves it out: rule 1 above and rules 3 to 10 below, and rules 16, 20, 21 and 24 of Writing a classed triple, or it waits on an expert's answer (annotations/questions_for_experts.md). This holds whether or not the ground truth schema has an entity class or predicate for it.

### Affects

- record at pool position 4: 03a09af3-081e-4db6-9e3b-ea7c0e3138bd
- record at pool position 7: d5477563-0415-4e65-ab7c-d4bc9ed809e5
- record at pool position 13: ab33f184-95f4-4f33-8f3d-c4a09ec525d3
- record at pool position 12: bb1fe4b0-6543-42e3-9386-acbab0b37ad4
- classed triple of the record at pool position 4: "MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0" (Dataset) DEVELOPED_BY_PARTY "NASA Ocean Biology Processing Group (OBPG)" (Organization)
- classed triple of the record at pool position 7: "MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006" (Dataset) DOCUMENTED_AT "https://landweb.modaps.eosdis.nasa.gov/knownissue?sensor=MODIS&sat=Terra&as=6" (WebPage)
- classed triple of the record at pool position 13: "ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0" (Dataset) REVISED_AFTER "September 2019 PSA/PDS external peer review" (Task)
- classed triple of the record at pool position 12: "Ensemble X-Ray Variability of AGN in 2XMMi-DR3" (Dataset) PRODUCED_USING_ALGORITHM "structure function (SF)" (Algorithm)
- rule: What counts as a fact, rule 2
- pipeline method: annotations/ground_truth_schema.txt: a new predicate for each fact found worth one
