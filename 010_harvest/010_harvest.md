# 010_harvest

Terms ([record](../docs/terminology.md#1-records-and-their-text), [metadata field](../docs/terminology.md#1-records-and-their-text), run, report, log, [manifest](../docs/terminology.md#8-the-pipeline), [origin](../docs/terminology.md#8-the-pipeline), …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Records and their text*.

## Purpose

Downloads the metadata of every catalog entry on [data.nasa.gov](https://data.nasa.gov) through its public CKAN API. This is the pipeline's only contact with the outside world: every later [step](../docs/terminology.md#8-the-pipeline) works from the files saved here, so a [harvest](../docs/terminology.md#1-records-and-their-text) is a snapshot of the catalog on the day it was taken.

Only metadata is downloaded (titles, descriptions, [maintainers](../docs/terminology.md#1-records-and-their-text), tags, formats, links). The scientific data the [records](../docs/terminology.md#1-records-and-their-text) point to is never fetched.

## To do

### Every step

- **Run it** after the [steps](../docs/terminology.md#8-the-pipeline) before it, and again whenever their outputs change (see *How to run*).
- **Before a step pays for [model calls](../docs/terminology.md#8-the-pipeline),** read what it prints: anything it can't do exactly as asked is listed above the question. Then press Enter to go ahead, or anything else to stop, having spent nothing. (Steps that call no [model](../docs/terminology.md#8-the-pipeline) don't ask.)
- **Read the [report](../docs/terminology.md#8-the-pipeline)'s Warnings:** the report is `outputs/reports/<step>_<date>_<time>.md` (the step prints its path when it ends). Each warning is explained, with what to do, in *Checks and warnings* below.
- **Commit every changed file in the `annotations/` folder to Git,** so your work is safe.

### This step

- **Don't make a small trial [harvest](../docs/terminology.md#1-records-and-their-text) first** (`--max_records`): splitting writes its file (`outputs/intermediate_results/030_split/splits.json`) only once, so a trial catalog would stay in it.
- Nothing else: the [step](../docs/terminology.md#8-the-pipeline) runs on its own (for how long, see *Known limits*).

## Inputs

None: the [step](../docs/terminology.md#8-the-pipeline) reads no input files. It downloads from `https://data.nasa.gov/api/3/action/package_search`.

## Outputs

In `outputs/intermediate_results/010_harvest/`:

**On a rerun:** pages that still fit this [run](../docs/terminology.md#8-the-pipeline)'s [settings](../docs/terminology.md#8-the-pipeline) are kept and only missing ones fetched; files beyond this run's range are deleted (see *How to run*).

| File | Contents |
|---|---|
| `batch_00000.json`, `batch_01000.json`, … | One file per page: the raw CKAN [records](../docs/terminology.md#1-records-and-their-text), exactly as the API returned them, wrapped with the request that returned them (see Audit trail). The number is the position of the page's first record. |
| `_manifest.json` | [Run id](../docs/terminology.md#8-the-pipeline), settings, input files and their hashes, output files and their hashes, headline numbers (records harvested) and the [harvest](../docs/terminology.md#1-records-and-their-text) date, which later [steps](../docs/terminology.md#8-the-pipeline) carry forward. Written when a run finishes. |

One [batch file](../docs/terminology.md#1-records-and-their-text), shortened:

```json
{"request": "GET https://data.nasa.gov/api/3/action/package_search?rows=1000&start=0&sort=metadata_created+asc%2C+id+asc",
 "fetched_at": "2026-09-27T10:16:03-07:00", "http_status": 200, "catalog_count": 36388,
 "run_id": "010_harvest_2026-09-27_1016",
 "records": [{"id": "a1b2…", "name": "modis-aqua-…", "title": "MODIS/Aqua …", "notes": "…",
              "maintainer": "Earthdata Forum", "tags": [{"name": "…"}], "resources": [{"format": "HDF"}], …},
             …]}
```

Each run also leaves `outputs/reports/<run id>.md` (the [report](../docs/terminology.md#8-the-pipeline): what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `page_size` | 1000 | [Records](../docs/terminology.md#1-records-and-their-text) per request | Rarely. 1000 is CKAN's usual maximum. Changing it means most [batch files](../docs/terminology.md#1-records-and-their-text) are downloaded again (see below). |
| `max_records` | 0 | Stop after this many records; 0 means the whole catalog | For a quick trial, e.g. `3` or `2000`. The folder is made to match the trial (see below); a later full [run](../docs/terminology.md#8-the-pipeline) keeps the pages that still fit and fetches the rest. |
| `pause_seconds` | 0.5 | Wait after each page downloaded | Raise it if the server starts refusing requests. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`):

```
py 010_harvest/run.py --help                   every setting, with its default
py 010_harvest/run.py                          whole catalog (37 pages)
py 010_harvest/run.py --max_records 2000       quick trial
```

**Paying.** This [step](../docs/terminology.md#8-the-pipeline) makes no [model calls](../docs/terminology.md#8-the-pipeline): it costs nothing, and keeps no cache. It needs the internet, and the `requests` package (installed with the environment).

**What a rerun does with the files already there.** Each page has a fixed file name, from the position of its first [record](../docs/terminology.md#1-records-and-their-text), and:

- a [batch file](../docs/terminology.md#1-records-and-their-text) is **kept** when its [request block](../docs/terminology.md#1-records-and-their-text) shows it was requested the same way (same page size, same start, same sort order) and it holds exactly the number of records its page needs in this [run](../docs/terminology.md#8-the-pipeline), so a rerun after a crash or Ctrl+C only fetches what's missing. Its records are not compared with the catalog as it is today;
- a batch file that doesn't fit is **downloaded again** and overwritten: one from a run with a different `max_records` or `page_size`, one saved in the old format without a request block, or one requested in another sort order. Every batch file saved before 010 switched to its fixed sort order is in that last group, including the [harvest](../docs/terminology.md#1-records-and-their-text) of 2026-09-27, so the next run downloads the whole catalog again;
- a batch file beyond this run's range is **deleted** at the end of the run, so later steps never read a mix of two harvests.

The first page is always requested, even when every file is kept: it tells the step how many records the catalog holds today. When a run finishes, the folder holds exactly this run's harvest; a run that stops part-way can leave files from an earlier run beyond the point it reached, until the next run finishes.

The [report](../docs/terminology.md#8-the-pipeline) counts all four cases (downloaded, kept, downloaded again, deleted). For a new snapshot, delete `outputs/intermediate_results/010_harvest/` first; otherwise kept pages may date from earlier days, and the report says so.

## How it works

Two [stages](../docs/terminology.md#8-the-pipeline), in `010_harvest/run.py`'s `main()`, both code:

1. **Download the catalog** (`download_catalog`). The first request learns the catalog's size; the [run](../docs/terminology.md#8-the-pipeline) aims for that many [records](../docs/terminology.md#1-records-and-their-text), or `max_records` if smaller. Pages are requested in order (`start` = 0, 1000, 2000, …), sorted oldest record first (by creation time, then id). CKAN's default order puts the most recently modified record first, so a record added or edited during the [harvest](../docs/terminology.md#1-records-and-their-text) would jump ahead of the pages already fetched: it would be missed, and every later page would shift and repeat a record. In creation order a new record lands at the end and an edit moves nothing. Each page is written as soon as it arrives, under a temporary name that is renamed when the write finishes, so a crash never leaves a half-written file behind.
   - Responses 429, 500, 502, 503 and 504, and failed connections or reads, are retried up to 5 times: the first retry straight away, then after 3, 6, 12 and 24 s, or after the wait the server asks for (a `Retry-After` header). When the retries run out, or on any other error (e.g. 404), the [step](../docs/terminology.md#8-the-pipeline) stops.
   - Each request waits up to 5 s to connect and up to 120 s for the response's data. On data.nasa.gov a page of 1,000 records took 23–52 s to arrive (2026-09-27).
   - An empty page before the target is reached ends the download early, with a warning.
2. **Check it's complete** (`check_complete`). Every saved record is counted and its `id` collected: the number saved is compared with the number the run aimed for; ids that appear twice and records with no id are counted; the catalog's size, as each page reported it, must not change; and every [batch file](../docs/terminology.md#1-records-and-their-text) must have its [request block](../docs/terminology.md#1-records-and-their-text).

**Then the results** (`results`): the batch files are already on disk; the [report](../docs/terminology.md#8-the-pipeline) gives record counts, batch files downloaded vs. kept, batch files with their request block, the [harvest date](../docs/terminology.md#1-records-and-their-text), and any warnings.

The code: `010_harvest/` holds `run.py` (the [control panel](../docs/terminology.md#8-the-pipeline): inputs, [settings](../docs/terminology.md#8-the-pipeline) and the moves, in order); `010_harvest/010_harvest_helpers/` holds `moves.py` (the moves, and writing the results), `ckan_client.py` (the API requests) and `batches.py` (the batch files). Shared with other steps: `common/common_helpers/files.py` (saving files).

## Prompts

None: this [step](../docs/terminology.md#8-the-pipeline) makes no [model calls](../docs/terminology.md#8-the-pipeline).

## Checks and warnings

**Shown before paying:** none, since this [step](../docs/terminology.md#8-the-pipeline) makes no [model calls](../docs/terminology.md#8-the-pipeline).

**In the [report](../docs/terminology.md#8-the-pipeline)**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *Saved N records but expected M* | Some pages weren't saved, or [records](../docs/terminology.md#1-records-and-their-text) were deleted from the catalog during the [harvest](../docs/terminology.md#1-records-and-their-text): each deletion shifts the later pages back by one, so one record is missed, and the last page comes back short. | Rerun: it fetches missing pages and the short last page, but not a record missed in the middle. For a complete snapshot, delete the folder and rerun. |
| *The catalog's size changed while the pages were fetched (from N to M records …)* | Records were added or deleted during the harvest. A deletion shifts the later pages back by one, so one record is missed, even when an addition keeps the total right. | For an exact snapshot, delete the folder and rerun. |
| *N records appear twice* | With pages in creation order, new and edited records shift nothing, so a repeat means a record reappeared in the middle of the order during the harvest (e.g. one restored after deletion), or that [batch files](../docs/terminology.md#1-records-and-their-text) kept from an earlier [run](../docs/terminology.md#8-the-pipeline) overlap the new ones. (The harvest of 2026-09-27, made in CKAN's default order, had 12 repeats, from records added or edited mid-harvest; that is what the fixed order prevents.) | 020_clean keeps the first copy. For a clean snapshot, delete the folder and rerun. |
| *The API returned an empty page before the reported count* | The catalog shrank during the harvest, or the API misbehaved. | Rerun later. |
| *N of M batch files were kept from an earlier run … between DATE and DATE* | A resumed harvest spans several days. | Fine for development. For a snapshot you'll cite, delete the folder and rerun. |
| *N batch files have no request block* | Should not happen: a file without one is downloaded again, so it means a batch file was replaced by hand during the run. | Rerun; the named files are fetched again. |
| *N record(s) have no id.* | Should not happen: CKAN gives every record an id. Such records can't be told apart from others; 020_clean drops them. | Look at the batch files to see which records they are. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *Max retries exceeded …* (e.g. *too many 503 error responses*), or a connection error | The API kept failing after 5 retries, or couldn't be reached. Pages already saved are kept. | Rerun later: only the missing pages are fetched. |
| *NNN Client Error …* (e.g. 404), or *CKAN reported failure for start=N* | The API refused the request. | Check the address (`URL` in `ckan_client.py`); retry later. |
| *data.nasa.gov returned a page that isn't JSON for start=N …* | The API answered with something else, e.g. a maintenance page. | Retry later. |
| *page_size must be at least 1* / *max_records must be at least 0* / *pause_seconds must be at least 0* | A [setting](../docs/terminology.md#8-the-pipeline) is out of range. | Fix the setting. |

**[Harvest date](../docs/terminology.md#1-records-and-their-text).** Recorded in the report and the [manifest](../docs/terminology.md#8-the-pipeline), and carried forward to every later step's report. It is the day the pages were fetched, read from each batch file's `fetched_at` (for a file without a [request block](../docs/terminology.md#1-records-and-their-text), the day the file was last changed), or a range of days if pages were kept from earlier runs.

## Audit trail

- **[Log](../docs/terminology.md#8-the-pipeline).** `outputs/logs/<run id>.log` records the command line, the [settings](../docs/terminology.md#8-the-pipeline), the git commit, every API request (URL, status, size, time), every retry, each [move](../docs/terminology.md#8-the-pipeline)'s duration, each output file's hash and, on failure, the full traceback. The console shows the same [run](../docs/terminology.md#8-the-pipeline) without the request-level detail.
- **[Origin](../docs/terminology.md#8-the-pipeline).** Each [batch file](../docs/terminology.md#1-records-and-their-text) holds the request that returned its [records](../docs/terminology.md#1-records-and-their-text): the URL, when it was fetched, the HTTP status, the catalog size the API reported, and the run that fetched it. A batch kept on a rerun keeps the [request block](../docs/terminology.md#1-records-and-their-text) of the run that fetched it. This is where every later item's origin chain ends. [Harvests](../docs/terminology.md#1-records-and-their-text) saved by an earlier version of this [step](../docs/terminology.md#8-the-pipeline), as a bare list with a separate `_lineage.jsonl`, are downloaded again on the next run, and the old `_lineage.jsonl` is deleted. (The harvest of 2026-09-27 was converted to this format in place, from its `_lineage.jsonl`, instead of being downloaded again. That older format didn't keep the catalog size per page, so in those files only `batch_00000.json` has a `catalog_count`.)
- **Trace a record.** `py helpers/audit.py <record id>` starts from the latest step that has the record (the highest-numbered step whose last run's output holds it: for a [ground truth](../docs/terminology.md#4-ground-truth-and-samples) record, e.g. 060's `extracted_triples.csv`, 050's newest [draft batch](../docs/terminology.md#4-ground-truth-and-samples) or 030's `splits.json`; otherwise 020's `records.jsonl`) and follows it back to the batch file that holds it, the run that fetched it, and the request that returned it.

## Known limits

- **Paging by position.** CKAN has no snapshot cursor. The fixed sort order stops new and edited [records](../docs/terminology.md#1-records-and-their-text) from shifting the pages, but a record deleted during the [harvest](../docs/terminology.md#1-records-and-their-text) still shifts every later page back by one, and the record that moves onto an already-fetched page is missed. A full harvest takes about 20–25 minutes (22 min 50 s on 2026-09-27, 37 pages). The catalog does change within hours: it reported 36,387 records at 17:00 on 2026-09-27 and 36,178 four hours later.
- **`extras` and nested [fields](../docs/terminology.md#1-records-and-their-text) are saved but unexplored.** The files keep every field as the API returns it; deciding what to use is left to later [steps](../docs/terminology.md#8-the-pipeline).
- **What has run against data.nasa.gov.** The full harvest of 2026-09-27 (36,387 records) was made by an earlier version of this step, in CKAN's default order and with a separate lineage file. The current version, with its fixed sort order, has run only against a stand-in API; one 3-record request confirmed that data.nasa.gov accepts the sort order and returns records oldest first. No harvest has been compared with one made by `to_be_reshaped/nasa_harvest.py`.
