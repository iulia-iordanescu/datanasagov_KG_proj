# Audit and observability

How to find out what a run did, what it read and wrote, and where any single item came from.

## Where to look

Every run of a step has a run id, e.g. `020_clean_2026-09-27_1030`: the step name and the minute it started, plus `-2`, `-3`, … for a second or third run started in the same minute. Everything the run leaves behind uses that id:

| File | Answers | Kept |
|---|---|---|
| `outputs/reports/<run id>.md` | What came out? Numbers, warnings, timeline, and links to the files below. And the run's full recipe: the Git commit (the code), the settings (the model among them), the prompts it filled in with a fingerprint of each one's exact text, and the inputs with the run that made each. | every run |
| `outputs/logs/<run id>.log` | What happened, in what order? Why did it fail? | every run |
| `outputs/intermediate_results/<step>/_manifest.json` | Exactly which files went in and came out: each with its sha256 hash, and the run that produced each input. | Removed when a run starts and written when it finishes, so it describes the last run that finished. If a run fails, the previous manifest is put back only if every file it lists still has the hash it recorded (e.g. a run stopped by a bad setting, which wrote nothing); otherwise the step has none until a run finishes. |
| The item's **origin**, inside the output file itself | Where did this item come from? | as long as the output file |

Start from the report: its **Run** section links to the log.

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
py helpers/audit.py <key>                                         a record id, or a schema entry's name
py helpers/audit.py <key> --step 010_harvest                      look in one step only
py helpers/audit.py --step 010_harvest --file batch_01000.json --position 17
```

`helpers/audit.py` finds the item in the latest step that has it (searching the output files each step's manifest lists, by the item's `id`, or its `name` for a schema entry), then follows its origin upstream, one step at a time, to the 010 batch file and the API request that first returned it. An origin can also point to a file kept in Git, such as the ground truth candidates pool in `annotations/`; the trace shows it as made by a person and goes no further up that branch. A JSON output holding several lists under their own names (030's `splits.json`) is searched in all of them. It shows at most 20 matches.

Each hop names a run, with its report and log: for a 010 batch file, the run recorded in the file (the one that fetched it); for any other file, the run in its step's manifest (the last run that finished). A step folder without a manifest is not searched, and hops through it show `made by run unknown`. Only the files a step's manifest lists are searched, i.e. those its last finished run wrote: for 050, the newest draft batch, not earlier ones. A record in an older draft batch is found in 030's `splits.json` instead, which leads back to the same harvest.

What the trace flags along the way:

- `[file has changed since: hash differs]`: the file an item was made from is no longer the one the step read (its hash differs from the one the step's manifest recorded for that input file). That usually means an earlier step was rerun and this step's output is out of date: rerun this step too.
- `[file no longer exists]`: the file an origin points to is gone.
- `(item not found there)`: the file exists, but has no item with that key or position.

## Origin format

There is no separate lineage file. Each output item names the input item(s) it came from, in the same file:

- JSON output: an `_origin` field. CSV output: an `origin` column, references joined with `; `.
- A reference is `<step>/<file>#<key>`, or `#<position>` (counting from 0) when the item has no key. Files kept in Git are named from the repo root, e.g. `annotations/ground_truth/batch_000.csv#17`. Paths always use forward slashes.

```json
{"id": "a1b2…", "title": "…", "notes": "…", "maintainer": "…",
 "_origin": ["010_harvest/batch_00000.json#a1b2…"]}
```

010 is where origin starts. Each batch file wraps its records, left exactly as the API sent them, with the request that returned them:

```json
{"request": "GET https://data.nasa.gov/api/3/action/package_search?rows=1000&start=0",
 "fetched_at": "2026-09-27T10:16:03-07:00", "http_status": 200, "catalog_count": 36388,
 "run_id": "010_harvest_2026-09-27_1016", "records": [ …raw CKAN records… ]}
```

The manifest is the per-file half of the audit trail: each input file's hash and the run that produced it are recorded there once, not repeated on every item.

## For developers: adding origin to a step

In a helper file:

```python
from common.audit import check_origins, log, origin

log.info("cleaned 36,289 records")                 # console + log file
log.debug(f"record {rid}: tier=conservative")      # log file only
record["_origin"] = [origin(batch_file, rid)]      # the file the item was read from, and its key
row["origin"] = "; ".join([origin("records", rid), origin("schema", "ABOARD")])
```

- `origin(source, key_or_position)`: `source` is the name of one of the step's `INPUTS` when that input is a single file, or the path of the input file the item came from (an input like `010_harvest/batch_*.json` has many files).
- Give every item its origin as it is produced.
- Check coverage before returning: `check_origins(items, "records")` returns a warning for any item without an origin, or `None`. Add it to the step's warnings.
