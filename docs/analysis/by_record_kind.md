# Scores by kind of record

Computed on 2026-11-13.

## What this is

The 20 evaluated records of the tuning part, grouped in two ways that need no judgment, with partial F1 per group on the ground truth of 2026-11-13. The runs are the six of `rescore_2026-11-13.md`.

Formula: partial F1 of a group = 2 × (exact pairs + partial pairs) ÷ (counted occurrences + ground truth triples), with each count summed over the group's records in one run (`070_evaluate/metrics/f1.md`). Counted occurrences are the occurrences less the untranslatable extracted triples and less those paired with a fact that waits on an expert. Each cell gives the mean of the three repeats, with the lowest and highest repeat in parentheses. Step 070 pools counts and never averages records' own numbers (`070_evaluate/metrics.md`, *Pooled, not averaged*). The column *Mean of the records' own partial F1* is the unweighted average over the group's records, given only to show how far a long record moves the pooled number.

**The groups are tiny.** They hold between 1 and 10 records, so every number here describes these 20 records and supports no claim about a kind of record in the catalog. The range in parentheses is the spread over three repeats on the same records, not a margin of error over records. No test was made between groups.

## By stratum

The stratum is the record's group of maintainers in `annotations/ground_truth_candidates.csv`, which step 030 used to draw the pool. It is the only field in the repository that sorts the evaluated records by where they come from: `organization` is "NASA" for all 20. Which data system a maintainer stands for is not recorded in the repository, so the strata are not relabelled here. Step 070 warns that the stratum *Planetary Data System* has none of the evaluated records while it is 17% of the pool.

| Stratum | Records | Ground truth triples | Partial F1, induced schema | Mean of the records' own partial F1, induced schema | Partial F1, ground truth schema |
|---|---:|---:|---:|---:|---:|
| Thomas Morgan | 7 | 100 | 63.9% (62.9% to 64.4%) | 64.7% | 84.8% (84.2% to 85.4%) |
| Earthdata Forum | 6 | 187 | 47.1% (46.5% to 48.0%) | 50.5% | 78.9% (78.2% to 80.0%) |
| NASA Space Physics Data Facility | 2 | 66 | 43.4% (41.9% to 46.3%) | 53.4% | 72.9% (68.9% to 76.8%) |
| (small maintainers) | 2 | 16 | 15.2% (14.8% to 15.4%) | 12.0% | 90.9% (89.7% to 93.3%) |
| NSIDC Services | 2 | 34 | 76.2% (74.6% to 78.7%) | 76.0% | 97.0% (95.5% to 98.5%) |
| HEASARC Help Desk | 1 | 29 | 36.6% (34.6% to 38.6%) | 36.6% | 71.2% (70.4% to 72.7%) |
| all evaluated records | 20 | 432 | 50.9% (50.7% to 51.0%) | 53.8% | 80.7% (80.0% to 81.4%) |

## By length of the record's text

The length is the number of characters of the record's text as step 060 sends it (script `prompt_sizes.py`). The split is at the median of the 20 records, 663.5 characters.

| Length of the text | Records | Ground truth triples | Partial F1, induced schema | Mean of the records' own partial F1, induced schema | Partial F1, ground truth schema |
|---|---:|---:|---:|---:|---:|
| at most 663.5 characters | 10 | 132 | 61.3% (60.4% to 62.1%) | 56.6% | 86.5% (85.7% to 87.4%) |
| more than 663.5 characters | 10 | 300 | 46.2% (45.8% to 46.7%) | 51.0% | 78.3% (77.3% to 78.8%) |
| all evaluated records | 20 | 432 | 50.9% (50.7% to 51.0%) | 53.8% | 80.7% (80.0% to 81.4%) |

In these 20 records, the 10 longer texts hold 300 of the 432 ground truth triples and have the lower pooled partial F1 with both schemas. Length and stratum are mixed, since the longest texts belong to few strata, so the two tables do not show two separate effects.

## Each record

Partial F1 with the induced schema is the mean of the record's own value over the three repeats (`metrics.json`, `per_record`).

| Pool position | Title | Stratum | Characters of text | Ground truth triples | Partial F1, induced schema |
|---:|---|---|---:|---:|---:|
| 0 | NASA Standards and and Technical Assistance Resource Tool | (small maintainers) | 423 | 8 | 0.0% |
| 1 | ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0 | Thomas Morgan | 303 | 11 | 66.6% |
| 2 | MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061 | NSIDC Services | 676 | 21 | 76.8% |
| 3 | Aquarius L3 Weekly Polar-Gridded Sea Surface Salinity V005 | NSIDC Services | 450 | 13 | 75.2% |
| 4 | MODIS Aqua Level 3 SST MID-IR 8 Day 4km Nighttime V2019.0 | Earthdata Forum | 2164 | 54 | 30.3% |
| 5 | DAWN GRAND MAP VESTA FAST NEUTRON RESIDUAL V1.0 | Thomas Morgan | 440 | 14 | 65.6% |
| 6 | MODIS/Terra+Aqua Land Aerosol Optical Depth Daily L2G Global 1km SIN Grid | Earthdata Forum | 565 | 17 | 72.0% |
| 7 | MODIS/Terra Land Surface Temperature/Emissivity Daily L3 Global 1km SIN Grid V006 | Earthdata Forum | 1503 | 34 | 48.6% |
| 9 | STARDUST 9P/TEMPEL 1 DFMI 2/3 NEXT V1.0 | Thomas Morgan | 502 | 25 | 67.8% |
| 10 | ROSETTA-ORBITER 67P/CAL ALICE 2 ESC1 V1.0 | Thomas Morgan | 272 | 9 | 90.2% |
| 12 | Ensemble X-Ray Variability of AGN in 2XMMi-DR3 | HEASARC Help Desk | 3104 | 29 | 36.6% |
| 13 | ROSETTA-ORBITER 67P OSINAC 4 ESC3-MTP020 RDR-INFLDSTR V1.0 | Thomas Morgan | 656 | 17 | 53.2% |
| 15 | Solar Orbiter Ephemeris, Heliocentric Trajectories, Heliographic, Heliographic Inertial, and Solar Ecliptic Coordinates, HelioWeb, Daily Data | NASA Space Physics Data Facility | 2583 | 11 | 68.8% |
| 16 | VG1 J/S/SS PWS EDITED SPECTRUM ANALYZER FULL RES V1.0 | Thomas Morgan | 671 | 14 | 58.3% |
| 18 | VIIRS/NPP BRDF/Albedo Parameter 3 Band M4 Daily L3 Global 30 ArcSec CMG V002 | Earthdata Forum | 1762 | 21 | 52.0% |
| 19 | BARREL 4G Rate Counter (RCNT) NaI Scintillator Diagnostics, Level 2, 4 s Data | NASA Space Physics Data Facility | 5885 | 55 | 38.0% |
| 21 | CH1-ORB MOON M3 2 L0 RAW NEAR-IR SPECTRAL IMAGES V1.0 | Thomas Morgan | 276 | 10 | 51.1% |
| 22 | Flight Data For Tail 655 | (small maintainers) | 286 | 8 | 24.0% |
| 24 | HIRDLS/Aura Level 3 Geopotential Height 1deg Lat Zonal Fourier Coefficients V007 (H3ZFCGPH) | Earthdata Forum | 1328 | 35 | 42.9% |
| 25 | OPERA Dynamic Surface Water Extent from Sentinel-1 (Version 1) | Earthdata Forum | 1312 | 26 | 57.1% |

## Where the numbers come from

Scripts `helpers/analysis/analyses.py` (function `by_kind`) and `helpers/analysis/tables.py`. They read each run's counts per record from `outputs/intermediate_results/070_evaluate/evaluations/` (one file per run: 070_evaluate_2026-11-13_1454, 070_evaluate_2026-11-13_1454-2, 070_evaluate_2026-11-13_1454-3, 070_evaluate_2026-11-13_1454-4, 070_evaluate_2026-11-13_1454-5, 070_evaluate_2026-11-13_1455), and each record's own partial F1 from the six `metrics.json` copied into `outputs/analysis/runs/`.
