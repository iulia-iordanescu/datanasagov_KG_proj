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
| `batch_00000.json`, `batch_01000.json`, … | One file per page: the raw CKAN records, exactly as the API returned them, wrapped with the request that returned them (see Audit trail). The number is the position of the page's first record. |
| `_manifest.json` | Run id, settings, every output file with its size and sha256 hash, the record count and the harvest date, for later steps (and, once it exists, the master report). Written only when a run finishes. |

One batch file, shortened:

```json
{"request": "GET https://data.nasa.gov/api/3/action/package_search?rows=1000&start=0",
 "fetched_at": "2026-09-27T10:16:03-07:00", "http_status": 200, "catalog_count": 36388,
 "run_id": "010_harvest_2026-09-27_1016",
 "records": [{"id": "a1b2…", "name": "modis-aqua-…", "title": "MODIS/Aqua …", "notes": "…",
              "maintainer": "Earthdata Forum", "tags": [{"name": "…"}], "resources": [{"format": "HDF"}], …},
             …]}
```

Each run also leaves, under its run id (e.g. `010_harvest_2026-09-27_1016`):

- `outputs/reports/<run id>.md`: the report, for people.
- `outputs/logs/<run id>.log`: everything that happened, in order, including every API request and retry.

## Settings

| Setting | Default | Meaning | When to change it |
|---|---|---|---|
| `page_size` | 1000 | Records per request | Rarely. 1000 is CKAN's usual maximum. Changing it means most batch files are downloaded again (see below). |
| `max_records` | 0 | Stop after this many records; 0 means the whole catalog | For a quick trial, e.g. `3` or `2000`. The folder is made to match the trial (see below); a later full run keeps the pages that still fit and fetches the rest. |
| `pause_seconds` | 0.5 | Wait after each page downloaded | Raise it if the server starts refusing requests. |

## How to run

From the repo root:

```
py 010_harvest.py                          whole catalog (37 pages, about 20-25 minutes)
py 010_harvest.py --max_records 2000       quick trial
py 010_harvest.py --help                   list settings
```

Needs the `requests` package, installed with the rest of the environment (`docs/virtual_environment_setup.md`).

**What a rerun does with the files already there.** Each page has a fixed file name, from the position of its first record, and:

- a batch file is **kept** when its request block shows it was requested the same way (same page size, same start, same sort order) and it holds exactly the number of records its page needs in this run, so a rerun after a crash or Ctrl+C only fetches what's missing. Its records are not compared with the catalog as it is today;
- a batch file that doesn't fit is **downloaded again** and overwritten: one from a run with a different `max_records` or `page_size`, one saved in the old format without a request block, or one requested in another sort order. Every batch file saved before 010 switched to its fixed sort order is in that last group, including the harvest of 2026-09-27, so the next run downloads the whole catalog again;
- a batch file beyond this run's range is **deleted** at the end of the run, so later steps never read a mix of two harvests.

The first page is always requested, even when every file is kept: it tells the step how many records the catalog holds today. When a run finishes, the folder holds exactly this run's harvest; a run that stops part-way can leave files from an earlier run beyond the point it reached, until the next run finishes.

The report counts all four cases (downloaded, kept, downloaded again, deleted). For a new snapshot, delete `outputs/intermediate_results/010_harvest/` first; otherwise kept pages may date from earlier days, and the report says so.

## How it works

1. **Download the catalog.** The first request learns the catalog's size; the run aims for that many records, or `max_records` if smaller. Pages are requested in order (`start` = 0, 1000, 2000, …), sorted oldest record first (by creation time, then id). CKAN's default order puts the most recently modified record first, so a record added or edited during the harvest would jump ahead of the pages already fetched: it would be missed, and every later page would shift and repeat a record. In creation order a new record lands at the end and an edit moves nothing. Each page is written as soon as it arrives, under a temporary name that is renamed when the write finishes, so a crash never leaves a half-written file behind.
   - Responses 429, 500, 502, 503 and 504, and failed connections or reads, are retried up to 5 times: the first retry straight away, then after 3, 6, 12 and 24 s, or after the wait the server asks for (a `Retry-After` header). When the retries run out, or on any other error (e.g. 404), the step stops.
   - Each request waits up to 5 s to connect and up to 120 s for the response's data. On data.nasa.gov a page of 1,000 records took 23–52 s to arrive (2026-09-27).
   - An empty page before the target is reached ends the download early, with a warning.
2. **Check it's complete.** Every saved record is counted and its `id` collected: the number saved is compared with the number the run aimed for; ids that appear twice and records with no id are counted; and every batch file must have its request block.
3. **Report.** Record counts, batch files downloaded vs. kept, batch files with their request block, the harvest date, and any warnings.

The code is in `010_harvest/`: `moves.py` (the three moves above), `ckan_client.py` (API requests), `batches.py` (batch files).

## Checks and warnings

| Message | Meaning | What to do |
|---|---|---|
| *Saved N records but expected M* | Some pages weren't saved, or records were deleted from the catalog during the harvest: each deletion shifts the later pages back by one, so one record is missed, and the last page comes back short. | Rerun: it fetches missing pages and the short last page, but not a record missed in the middle. For a complete snapshot, delete the folder and rerun. |
| *N records appear twice* | With pages in creation order, new and edited records shift nothing, so a repeat means a record reappeared in the middle of the order during the harvest (e.g. one restored after deletion), or that batch files kept from an earlier run overlap the new ones. (The harvest of 2026-09-27, made in CKAN's default order, had 12 repeats, from records added or edited mid-harvest; that is what the fixed order prevents.) | 020_clean keeps the first copy. For a clean snapshot, delete the folder and rerun. |
| *The API returned an empty page before the reported count* | The catalog shrank during the harvest, or the API misbehaved. | Rerun later. |
| *N batch files were kept from an earlier run … between DATE and DATE* | A resumed harvest spans several days. | Fine for development. For a snapshot you'll cite, delete the folder and rerun. |
| *N batch files have no request block* | Should not happen: a file without one is downloaded again, so it means a batch file was replaced by hand during the run. | Rerun; the named files are fetched again. |

**Harvest date.** Recorded in the report and the manifest, and carried forward to every later step's report. It is the day the pages were fetched, read from each batch file's `fetched_at`, or a range of days if pages were kept from earlier runs.

## Audit trail

- **Log.** `outputs/logs/<run id>.log` records the command line, settings, git commit, every API request (URL, status, size, time), every retry, each move's duration, each output file's hash, and on failure the full traceback. The console shows the same run without the request-level detail.
- **Origin.** Each batch file holds the request that returned its records: the URL, when it was fetched, the HTTP status, the catalog size the API reported, and the run that fetched it. A batch kept on a rerun keeps the request block of the run that fetched it. This is where every later item's origin chain ends. Harvests saved by an earlier version of this step, as a bare list with a separate `_lineage.jsonl`, are downloaded again on the next run, and the old `_lineage.jsonl` is deleted. (The harvest of 2026-09-27 was converted to this format in place, from its `_lineage.jsonl`, instead of being downloaded again. That older format didn't keep the catalog size per page, so in those files only `batch_00000.json` has a `catalog_count`.)
- **Trace a record.** `py audit.py <record id>` starts from the latest step that has the record (for a record in the ground truth candidates pool, 030's `splits.json`, or 050's newest draft batch if it's in it; otherwise 020's `records.jsonl`) and follows it back to the batch file that holds it, the run that fetched it, and the request that returned it.

## Human work

None.

## Known limits

- **Paging by position.** CKAN has no snapshot cursor. The fixed sort order stops new and edited records from shifting the pages, but a record deleted during the harvest still shifts every later page back by one, and the record that moves onto an already-fetched page is missed. A full harvest takes about 20–25 minutes (22 min 50 s on 2026-09-27, 37 pages). The catalog does change within hours: it reported 36,387 records at 17:00 on 2026-09-27 and 36,178 four hours later.
- **`extras` and nested fields are saved but unexplored.** The files keep every field as the API returns it; deciding what to use is left to later steps.
- **What has run against data.nasa.gov.** The full harvest of 2026-09-27 (36,387 records) was made by an earlier version of this step, in CKAN's default order and with a separate lineage file. The current version, with its fixed sort order, has run only against a stand-in API; one 3-record request confirmed that data.nasa.gov accepts the sort order and returns records oldest first. No harvest has been compared with one made by `nasa_harvest.py`.
