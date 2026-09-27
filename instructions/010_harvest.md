# 010_harvest

## Purpose

Downloads the metadata of every catalog entry on [data.nasa.gov](https://data.nasa.gov) through its public CKAN API. This is the pipeline's only contact with the outside world: every later step works from the files saved here, so a harvest is a snapshot of the catalog on the day it was taken.

Only metadata is downloaded (titles, descriptions, maintainers, tags, formats, links). The scientific data the records point to is never fetched.

## Inputs

None. The step reads `https://data.nasa.gov/api/3/action/package_search`.

## Outputs

In `outputs/intermediate_results/010_harvest/`:

| File | Contents |
|---|---|
| `batch_00000.json`, `batch_01000.json`, … | One file per page. Each is a JSON list of raw CKAN records, exactly as the API returned them. The number is the position of the page's first record. |
| `_lineage.jsonl` | One line per saved record, linking it to the API request that returned it (see Audit trail). |
| `_manifest.json` | Run id, settings, every output file with its sha256 hash, record count and harvest date, for later steps and the master report. |

One record, shortened:

```json
{"id": "a1b2…", "name": "modis-aqua-…", "title": "MODIS/Aqua …", "notes": "…",
 "maintainer": "Earthdata Forum", "tags": [{"name": "…"}], "resources": [{"format": "HDF"}], …}
```

Each run also leaves, under its run id (e.g. `010_harvest_2026-09-27_1016`):

- `outputs/reports/<run id>.md`: the report, for people.
- `outputs/logs/<run id>.log`: everything that happened, in order, including every API request and retry.

## Settings

| Setting | Default | Meaning | When to change it |
|---|---|---|---|
| `page_size` | 1000 | Records per request | Rarely. 1000 is CKAN's usual maximum. Changing it replaces the batch files already in the folder. |
| `max_records` | 0 | Stop after this many records; 0 means the whole catalog | For a quick trial, e.g. `3` or `2000`. The folder is made to match the trial (see below); a later full run keeps the pages that still fit and fetches the rest. |
| `pause_seconds` | 0.5 | Wait between requests | Raise it if the server starts refusing requests. |

## How to run

From the repo root:

```
py 010_harvest.py                          whole catalog (about 36 pages, a few minutes)
py 010_harvest.py --max_records 2000       quick trial
py 010_harvest.py --help                   list settings
```

Needs `requests` (`pip install requests`).

**What a rerun does with the files already there.** The folder always ends up holding exactly this run's harvest:

- a batch file that fits this run's settings is **kept** (so a rerun after a crash or Ctrl+C only fetches what's missing);
- a batch file that doesn't fit, e.g. from a run with a different `max_records` or `page_size`, is **downloaded again** and overwritten;
- a batch file beyond this run's range is **deleted**, so later steps never read a mix of two harvests.

The report counts all three. For a new snapshot, delete `outputs/intermediate_results/010_harvest/` first; otherwise kept pages may date from earlier days, and the report says so.

## How it works

1. **Download the catalog.** The first request learns the catalog's size. Then pages are requested in order (`start` = 0, 1000, 2000, …) until that many records are saved. Each page is written as soon as it arrives, under a temporary name that is renamed when the write finishes, so a crash never leaves a half-written file behind. Busy or failing responses (429, 5xx) are retried up to 5 times with growing pauses.
2. **Check it's complete.** Every saved record is counted and its `id` collected: the number saved must match the number the API reported, and no id should appear twice.
3. **Report.** Record counts, batch files downloaded vs. kept, records with lineage, the harvest date, and any warnings.

The code is in `010_harvest/`: `moves.py` (the three moves above), `ckan_client.py` (API requests), `batches.py` (batch files).

## Checks and warnings

| Message | Meaning | What to do |
|---|---|---|
| *Saved N records but expected M* | Some pages were not saved. | Rerun; it fetches only the missing pages. |
| *N records appear twice, and probably as many were skipped* | Records were added to the catalog during the harvest, shifting every later page by that many positions. | Usually harmless for a few records: 020_clean drops the repeats. For an exact snapshot, delete the folder and rerun. |
| *The API returned an empty page before the reported count* | The catalog shrank during the harvest, or the API misbehaved. | Rerun later. |
| *N batch files were kept from an earlier run … between DATE and DATE* | A resumed harvest spans several days. | Fine for development. For a snapshot you'll cite, delete the folder and rerun. |

| *N saved records have no lineage row* | Batch files kept from an earlier run have no lineage (e.g. `_lineage.jsonl` was deleted, or they came from `nasa_harvest.py`). | Delete the named batch files and rerun to fetch them again with lineage. |

**Harvest date.** Recorded in the report and the manifest, and carried forward to every later step's report. It is the day the pages were fetched, read from the lineage, or a range of days if pages were kept from earlier runs.

## Audit trail

- **Log.** `outputs/logs/<run id>.log` records the command line, settings, git commit, every API request (URL, status, size, time), every retry, each move's duration, each output file's hash, and on failure the full traceback. The console shows the same run without the request-level detail.
- **Lineage.** Each record in a batch file has one line in `_lineage.jsonl`:

  ```json
  {"run_id": "010_harvest_2026-09-27_1016",
   "output": {"file": "batch_01000.json", "position": 17, "key": "a1b2…"},
   "sources": [{"kind": "api", "request": "GET https://data.nasa.gov/api/3/action/package_search?rows=1000&start=1000",
                "fetched_at": "2026-09-27T10:16:04-07:00", "http_status": 200, "position": 17}]}
  ```

  A line is written before its batch file is saved, so every batch on disk has its lineage. A batch kept on a rerun keeps the lineage of the run that fetched it.
- **Trace a record.** `py audit.py <record id>` shows which batch file holds it, which run saved it, and the request that returned it. Once later steps exist, it follows the record through them too.

## Human work

None.

## Known limits

- **Paging by position.** CKAN has no snapshot cursor, so records added or removed mid-harvest shift the pages (see the warning above). A harvest of ~36 pages takes a few minutes, so this is rare.
- **`extras` and nested fields are saved but unexplored.** The files keep every field as the API returns it; deciding what to use is left to later steps.
- **Tested against a stand-in API only.** The first run against data.nasa.gov itself should be compared with the last harvest from `nasa_harvest.py` (same record count, same ids), before the old script is retired.
