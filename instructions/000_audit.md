# Audit and observability

How to find out what a run did, what it read and wrote, and where any single item came from.

## Where to look

Every run of a step has a run id, e.g. `020_clean_2026-09-27_1030`: the step name and the time it started. Everything the run leaves behind uses that id:

| File | Answers | Kept |
|---|---|---|
| `outputs/reports/<run id>.md` | What came out? Numbers, warnings, timeline, and links to the files below. | every run |
| `outputs/logs/<run id>.log` | What happened, in what order? Why did it fail? | every run |
| `outputs/intermediate_results/<step>/_manifest.json` | Exactly which files went in and came out: each with its sha256 hash, and the run that produced each input. | latest successful run |
| `outputs/intermediate_results/<step>/_lineage.jsonl` | Where did each output item come from? | latest run that wrote each output file |

Start from the report: its **Run** section links to the log and the lineage.

## Reading a log

```
2026-09-27 10:16:03.412  INFO     010_harvest  -- download_catalog
2026-09-27 10:16:04.735  DEBUG    010_harvest  GET https://data.nasa.gov/...&start=1000 -> 200, 3,412,118 bytes in 1.32 s
2026-09-27 10:16:40.021  WARNING  010_harvest  1 record appears twice, ...
2026-09-27 10:16:40.025  ERROR    010_harvest  failed: RetryError: ...
```

- `-- name` lines mark the start of each main move; the matching `-- name done in N s` gives its duration.
- `DEBUG` lines are detail the console doesn't show: requests, retries, file hashes, the full traceback.
- To find what went wrong, search for `ERROR`, then read the `full traceback` below it.

## Tracing an item

```
py audit.py <key>                                         a record id, a triple id, ...
py audit.py <key> --step 010_harvest                      look in one step only
py audit.py --step 010_harvest --file batch_01000.json --position 17
```

`audit.py` finds the item in the latest step whose lineage has it, then follows its sources upstream, one step at a time, down to the API request that first returned it. Each hop names the run that made it, with that run's report and log.

If the file an item was made from has changed since (its hash no longer matches what the lineage recorded), the trace flags it: `[file has changed since: hash differs]`. That usually means an earlier step was rerun and this step's output is now out of date: rerun this step too.

## Lineage format

One JSON object per line, one line per output item:

```json
{"run_id": "020_clean_2026-09-27_1030",
 "output":  {"file": "records.jsonl", "position": 412, "key": "a1b2…"},
 "sources": [{"kind": "file", "file": "outputs/intermediate_results/010_harvest/batch_00000.json",
              "sha256": "41724e…", "run_id": "010_harvest_2026-09-27_1016",
              "position": 412, "key": "a1b2…"}]}
```

Positions count from 0. A source of `"kind": "api"` (010 only) gives the request URL, when it was fetched, and the HTTP status instead of a file.

## For developers: adding lineage to a step

In a helper file:

```python
from common.audit import file_source, lineage, log

log.info("cleaned 36,289 records")                 # console + log file
log.debug(f"record {rid}: tier=conservative")      # log file only
lineage().add("records.jsonl", n, rid, [file_source(batch_file, pos, rid)])
```

- Add the row as each item is produced, before the output file is saved.
- `file_source` fills in the input file's hash and producing run; it caches them, so calling it per item is cheap.
- `run_step` finishes the lineage file automatically from the files in `Results.files`. A step that keeps files from an earlier run calls `lineage().keep(file)` and finishes the lineage itself (see `010_harvest/moves.py`).
- Check coverage: every output item should have a row. Warn if not.
