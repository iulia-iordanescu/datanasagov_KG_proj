# Audit and observability

How to find out what a [run](../docs/terminology.md#8-the-pipeline) did, what it read and wrote, and where any single item came from.

## Where to look

Every [run](../docs/terminology.md#8-the-pipeline) of a [step](../docs/terminology.md#8-the-pipeline) has a [run id](../docs/terminology.md#8-the-pipeline), e.g. `020_clean_2026-09-27_1030`: the step name and the minute it started, plus `-2`, `-3`, … for a second or third run started in the same minute. Everything the run leaves behind uses that id:

| File | Answers | Kept |
|---|---|---|
| `outputs/reports/<run id>.md` | What came out? Numbers, warnings, timeline, and links to the files below. And the run's full recipe: the Git commit (the code), the [settings](../docs/terminology.md#8-the-pipeline) (the [model](../docs/terminology.md#8-the-pipeline) among them), the prompts it filled in with a [fingerprint](../docs/terminology.md#8-the-pipeline) of each one's exact text, and the inputs with the run that made each, or, for a file kept in Git (e.g. in `annotations/`), a note when it has changes not committed to Git, which the Git commit then doesn't hold. | every run |
| `outputs/logs/<run id>.log` | What happened, in what order? Why did it fail? | every run |
| `outputs/intermediate_results/<step>/_manifest.json` | Exactly which files went in and came out: each with its sha256 hash (an input of several files, such as the [ground truth](../docs/terminology.md#4-ground-truth-and-samples)'s [batch files](../docs/terminology.md#4-ground-truth-and-samples): each file's name and length hash with its bytes, so a renamed file counts as changed; manifests before 2026-11-01 hashed the bytes alone), each input file's own sha256 (`file_hashes`, which the status compares, so the change of method on 2026-11-01 makes no input look changed), for 030's `splits.json` also the hash of what it holds without the id of the run that drew it (`content_sha256`), whether the input was given on the command line in place of its default (`given`), and the run that produced each input. The inputs are hashed again when the run ends: one that changed while the step ran stops the run, with no manifest (step 050 checks them also just before it writes its [drafted batch](../docs/terminology.md#4-ground-truth-and-samples)). | Removed when a run starts and written when it finishes, so it describes the last run that finished. If a run fails, the previous [manifest](../docs/terminology.md#8-the-pipeline) is put back only if every output file it lists still has the hash it recorded (e.g. a run stopped by a bad setting, which wrote nothing); otherwise the step has none until a run finishes. |
| `outputs/intermediate_results/<step>/previous_runs/<run id>/` | What did an earlier run produce, before a later run changed it? The earlier version of every output file a later run changed or removed, with that earlier run's manifest. A file a later run left as it was isn't kept a second time, so nothing is stored twice (code: `_keep_previous` and `_settle_previous` in `common/common_helpers/step.py`). | every earlier version, until you delete it |
| `outputs/intermediate_results/<step>/discarded.jsonl` | What did this run discard, and why? One line per item a stage removed, filtered, skipped, capped, folded into another or whose value it replaced (*Items discarded*, below). | every run of a pipeline step, rewritten each run |
| The item's **[origin](../docs/terminology.md#8-the-pipeline)**, inside the output file itself | Where did this item come from? | as long as the output file |

Start from the [report](../docs/terminology.md#8-the-pipeline): its **Run** section links to the [log](../docs/terminology.md#8-the-pipeline).

## Reading a log

```
2026-09-27 10:16:03.412  INFO     010_harvest  -- download_catalog
2026-09-27 10:16:04.735  DEBUG    010_harvest  GET https://data.nasa.gov/...&start=1000 -> 200, 3,412,118 bytes in 1.32 s
2026-09-27 10:16:40.021  WARNING  010_harvest  1 record appears twice, ...
2026-09-27 10:16:40.025  ERROR    010_harvest  failed: RetryError: ...
```

- `-- name` lines mark the start of each main [move](../docs/terminology.md#8-the-pipeline); the matching `-- name done in N s` gives its duration.
- `DEBUG` lines are detail the console doesn't show: requests, retries, file hashes, the full traceback.
- To find what went wrong, search for `ERROR`, then read the `full traceback` below it.

## Tracing an item

```
py helpers/audit.py <key>                                         a record id, or a schema entry's component class
py helpers/audit.py <key> --step 010_harvest                      look in one step only
py helpers/audit.py --step 010_harvest --file batch_01000.json --position 17
```

`helpers/audit.py` finds the item in the latest [step](../docs/terminology.md#8-the-pipeline) that has it (searching the output files each step's [manifest](../docs/terminology.md#8-the-pipeline) lists, by the item's `id`, or its `component_class` for a [schema entry](../docs/terminology.md#3-schemas)), then follows its [origin](../docs/terminology.md#8-the-pipeline) upstream, one step at a time, to the 010 [batch file](../docs/terminology.md#1-records-and-their-text) and the API request that first returned it. An origin can also point to a file kept in Git, such as the [ground truth candidates pool](../docs/terminology.md#4-ground-truth-and-samples) in `annotations/`; the trace shows it as made by a person and goes no further up that branch. A JSON output holding several lists under their own names (030's `splits.json`) is searched in all of them. It shows at most 20 matches.

Each hop names a [run](../docs/terminology.md#8-the-pipeline), with its [report](../docs/terminology.md#8-the-pipeline) and log: for a 010 batch file, the run recorded in the file (the one that fetched it); for any other file, the run in its step's manifest (the last run that finished). A step folder without a manifest is not searched, and hops through it show `made by run unknown`. Only the files a step's manifest lists are searched, i.e. those its last finished run wrote: for 050, the newest [drafted batch](../docs/terminology.md#4-ground-truth-and-samples), not earlier ones. A [record](../docs/terminology.md#1-records-and-their-text) in an older drafted batch is found in 030's `splits.json` instead, which leads back to the same [harvest](../docs/terminology.md#1-records-and-their-text). Under each hop's file, one line says what made it: `made by run <run id>` (or `made by run unknown`), then a hop for each origin; or, at the end of a branch, `kept in Git, made by a person: <path>`, `from the API: <request>, fetched <time>, HTTP <status>` (a 010 batch file's [request block](../docs/terminology.md#1-records-and-their-text)), or `no origin recorded`.

What the trace flags along the way:

- `[file has changed since: hash differs]`: the file an item was made from is no longer the one the step read (its hash differs from the one the step's manifest recorded for that input file). That usually means an earlier step was rerun and this step's output is out of date: rerun this step too.
- `[file no longer exists]`: the file an origin points to is gone.
- `(item not found there)`: the file exists, but has no item with that key or position.

## Items discarded

Nothing a stage of a step discards goes without a record: every pipeline step writes, on every run that finishes, `outputs/intermediate_results/<step>/discarded.jsonl`, one JSON object per line for each item one of its stages removed, filtered, skipped, capped, folded into another item or whose value it replaced (decided on 2026-11-15; `docs/improvements.md`). The file is listed among the run's outputs in its manifest, and is empty when the run discarded nothing, so a file from an earlier run never stays. A run that stops, fails or is interrupted after its stages discarded items (a file deleted or written over before the stop among them) writes them to `outputs/logs/<run id>_discarded.jsonl` instead, beside its log, each line marked with the run's status (`run_status`), and its report names that file under *Run*; the output folder's `discarded.jsonl` stays the last finished run's, which the manifest restored after the stop lists. Each line:

| Field | What it holds |
|---|---|
| `stage` | The stage that discarded it, as the step's `moves.py` names it, e.g. `stage 2 (extract_triple_instances)`; `model calls (<cache>)` or `model calls` for an answer of the model set aside before any stage read it (a saved answer of the wrong shape, asked again; a reply asked once more). |
| `action` | `discarded` (removed, filtered, skipped or capped), `folded` (a duplicate or a merge: the item is now counted as another one, named in `kept_as`) or `replaced` (a value the stage replaced; the item it belongs to is kept, `kept_as` holds the new value). |
| `item_type` | What the item is, in the words of `docs/terminology.md`: record, text, [triple instance](../docs/terminology.md#2-triples), [classed triple](../docs/terminology.md#2-triples), label, [predicate split](../docs/terminology.md#5-learning-the-schema-step-040), [schema entry](../docs/terminology.md#3-schemas), row of the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070), … |
| `reason` | Which check discarded it, in words. |
| `setting` | When a setting decided it: the setting and its value, e.g. `{"max_new_predicates": 50}`. |
| `record_id` | When the item belongs to one record. |
| `item` | The item's own words and values (a reply's item as the model wrote it, under `raw`, when it wasn't of the shape asked for). |
| `kept_as` | For `folded` and `replaced`: what it was folded into, or its new value. |
| `where` | When the item came from a file: the file and its position or line. |

The run's report has a section *Items discarded*, the same in every step: the items counted by stage, item type, action and reason, with the file's path. Where a stage takes items in and keeps some, it checks that the items in equal those kept plus those recorded as discarded or folded; if they don't, an item vanished without a record, which is a fault in the step's code: the run stops, naming the stage and the three counts, and writes no manifest for its outputs. Which items each step records, and which of its stages check: the row `discarded.jsonl` of each step's *Outputs*. The code: `common/common_helpers/dropped.py` (`discard`, `fold`, `replace`, `account`), written and reported by `run_step` (`common/common_helpers/step.py`).

To find an item: open the file in any editor and search for its record id or its words.

## Tracing what step 040 did with a predicate

```
py helpers/audit.py --induction "<regex>"                e.g. "aboard|on board"
py helpers/audit.py --induction "<regex>" --limit 100    show more (default 30)
py helpers/audit.py --induction "<regex>" --folder outputs/intermediate_results/040_induce_schema/previous_runs/<run id>
```

Why is a predicate I expected (e.g. one of the [ground truth schema](../docs/terminology.md#3-schemas)) not in the [induced schema](../docs/terminology.md#5-learning-the-schema-step-040)? `--induction` reads step 040's `the_schema.json` and `induction_evidence.json` (no [model call](../docs/terminology.md#8-the-pipeline); it writes nothing) and lists every [triple instance](../docs/terminology.md#2-triples) whose [predicate instance](../docs/terminology.md#2-triples), [source text](../docs/terminology.md#1-records-and-their-text), predicate label, or final predicate matches the regular expression (case ignored; `|` separates alternatives). Code: `common/common_helpers/induction_trace.py`. For each triple instance:

- `<record id>  "subject instance" -- "predicate instance" -- "object instance"`: the record whose text states it, and the triple instance as stage 2 extracted it.
- `source text: "…"`: its source text, cut at 220 characters.
- Its predicate's path: `label X` (stage 3) `-> merged into Y (stage 4)` `-> spelling fold to Z (stage 4)` `-> split to W by its object's entity class, C (stage 5)` (or by its subject's [entity class](../docs/terminology.md#3-schemas), or by its pattern, `S -> O`, the grouping its predicate was split by; an evidence file written before 2026-11-15 splits by the object's entity class only) `-> merged again into V (stage 5)` `= <final predicate>: IN THE SCHEMA`, `DEFERRED (<reason>)`, `found, but neither in the schema nor deferred` (should never happen: 040 puts every predicate it counts in one of the two), or `NOT FOUND in the counts` (the final predicate isn't among those stage 6 counted; should never happen either, unless the two files come from different runs); the first that applies in the order IN THE SCHEMA, DEFERRED, found, NOT FOUND; then the final predicate's support and how many maintainers back it. Stage 4 records each merge with the label at the end of its chain, so a chain A -> B -> C shows as A -> C. Instead of a path: `UNVERIFIED (<errors>)` for an unverified triple instance, or `no label: <why>` for a predicate instance without a label, `<why>` being `the service refused to label it (<its reason>)`, `the model left it unlabeled, even asked twice`, or ``not in `labels` (was 040 run with this text?)``, the first that applies, in that order; neither counts toward any predicate.

Then a summary: how many matched triple instances end in each final predicate, with its status, its support, and up to three of its predicate instances. If nothing matches, no triple instance of the run has the words: the model put the relationship in other words (try a wider expression), or extracted no triple instance for it. The evidence keeps triple instances, not the records' texts, so a text that states the relationship without a triple instance for it isn't found.

## Origin format

There is no separate lineage file. Each output item names the input item(s) it came from, in the same file:

- JSON output: an `_origin` field. CSV output: an `origin` column, references joined with `; `.
- A reference is `<step>/<file>#<key>`, or `#<position>` (counting from 0) when the item has no key. Files kept in Git are named from the repo root, e.g. `annotations/ground_truth/batch_000.csv#17`. Paths always use forward slashes.

```json
{"id": "a1b2…", "title": "…", "notes": "…", "maintainer": "…",
 "_origin": ["010_harvest/batch_00000.json#a1b2…"]}
```

010 is where [origin](../docs/terminology.md#8-the-pipeline) starts. Each [batch file](../docs/terminology.md#1-records-and-their-text) wraps its [records](../docs/terminology.md#1-records-and-their-text), left exactly as the API sent them, with the request that returned them:

```json
{"request": "GET https://data.nasa.gov/api/3/action/package_search?rows=1000&start=0",
 "fetched_at": "2026-09-27T10:16:03-07:00", "http_status": 200, "catalog_count": 36388,
 "run_id": "010_harvest_2026-09-27_1016", "records": [ …raw CKAN records… ]}
```

The [manifest](../docs/terminology.md#8-the-pipeline) is the per-file half of the audit trail: each input file's hash and the [run](../docs/terminology.md#8-the-pipeline) that produced it are recorded there once, not repeated on every item.

## For developers: adding origin to a step

In a helper file:

```python
from common.audit import check_origins, log, origin

log.info("cleaned 36,289 records")                 # console + log file
log.debug(f"record {rid}: tier=conservative")      # log file only
record["_origin"] = [origin(batch_file, rid)]      # the file the item was read from, and its key
row["origin"] = "; ".join([origin("records", rid), origin("schema", "ABOARD")])
```

- `origin(source, key_or_position)`: `source` is the name of one of the [step](../docs/terminology.md#8-the-pipeline)'s `INPUTS` when that input is a single file, or the path of the input file the item came from (an input like `010_harvest/batch_*.json` has many files).
- Give every item its [origin](../docs/terminology.md#8-the-pipeline) as it is produced.
- Check coverage before returning: `check_origins(items, "records")` returns a warning for any item without an origin, or `None`. Add it to the step's warnings.
