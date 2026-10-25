# 060_extract

Terms ([classed triple](../docs/terminology.md#2-triples), [entity class](../docs/terminology.md#3-schemas), [schema](../docs/terminology.md#3-schemas), [pattern](../docs/terminology.md#3-schemas), [describes triple](../docs/terminology.md#2-triples), [error](../docs/terminology.md#2-triples), [flag](../docs/terminology.md#2-triples), [schema additions](../docs/terminology.md#3-schemas), …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Extracting with a schema (step 060)*.

## Purpose

Extracts, from each [record](../docs/terminology.md#1-records-and-their-text)'s [text](../docs/terminology.md#1-records-and-their-text), the [facts](../docs/terminology.md#2-triples) a [schema](../docs/terminology.md#3-schemas) can express. A [model](../docs/terminology.md#8-the-pipeline) lists them as [classed triples](../docs/terminology.md#2-triples) using **only** the schema's [entity classes](../docs/terminology.md#3-schemas) and [predicates](../docs/terminology.md#3-schemas), finding each [subject instance](../docs/terminology.md#2-triples) and [object instance](../docs/terminology.md#2-triples) in the text itself ([end-to-end extraction](../docs/terminology.md#6-extracting-with-a-schema-step-060)). Code checks every one against the record's text and the schema, then keeps it or removes it with a reason. What 060 keeps is what [step](../docs/terminology.md#8-the-pipeline) 070 evaluates against the [ground truth](../docs/terminology.md#4-ground-truth-and-samples), and what step 080 will build the graph from.

The schema is the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060): by default, 040's [induced schema](../docs/terminology.md#5-learning-the-schema-step-040) plus the [schema additions](../docs/terminology.md#3-schemas), the entity classes, predicates, and [patterns](../docs/terminology.md#3-schemas) you write in `annotations/schema_additions.txt` (e.g. on a mentor's advice). By default, 060 extracts only from the [finished records](../docs/terminology.md#4-ground-truth-and-samples), the ones 070 can evaluate. Once the schema is final, `--extract_from all` extracts from every record.

## To do

What to do, and when, is in [`docs/upkeep.md`](../docs/upkeep.md), one page for every step; `py run_pipeline.py --status` (or the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples)'s home page) lists what is waiting now. For this step, in short:

- Choose the model before the real runs ([*Before the first run*](../docs/upkeep.md#before-the-first-run)).
- Before each run, read what the model is given: the rules (`common/common_prompts/extraction_rules.txt`) and the prompts (*Prompts*, below) ([*Before the first run*](../docs/upkeep.md#before-the-first-run)).
- Run it again after finishing more [ground truth](../docs/terminology.md#4-ground-truth-and-samples) records, and consider, for the [schema additions](../docs/terminology.md#3-schemas), the [component classes](../docs/terminology.md#3-schemas) outside the schema it used, from [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) only ([*After step 060*](../docs/upkeep.md#after-step-060)).
## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned [records](../docs/terminology.md#1-records-and-their-text): the [texts](../docs/terminology.md#1-records-and-their-text). |
| `splits` | `030_split/splits.json` | Which [pool](../docs/terminology.md#4-ground-truth-and-samples) records are tuning and which held-out: a [schema entry](../docs/terminology.md#3-schemas) of `annotations/schema_additions.txt` learned from the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) is used only if it names [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070). |
| `schema` | `040_induce_schema/the_schema.json` | The [schema](../docs/terminology.md#3-schemas) to extract with. Any schema in one of the two shapes below can be given instead: `--schema <file>`. |
| `additions` | `./annotations/schema_additions.txt` (in Git) | The [schema additions](../docs/terminology.md#3-schemas): [entity classes](../docs/terminology.md#3-schemas), [predicates](../docs/terminology.md#3-schemas), and patterns added to whichever schema is used. Starts empty. |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | Which records have ground truth, and which are finished. Needed only with `extract_from` `ground_truth` (the default): with `all`, or with `ids`, no files yet is fine. |

### The shape of a schema

A [schema](../docs/terminology.md#3-schemas) holds [entity classes](../docs/terminology.md#3-schemas) and [predicates](../docs/terminology.md#3-schemas), each with a one-line definition, and [patterns](../docs/terminology.md#3-schemas). 060 reads two shapes, told apart by the file's ending (`common/common_helpers/schema_io.py`).

**JSON (`.json`), like 040's `the_schema.json`.** Only each entry's `"component_class"` is required, but give each a definition: it's the [model](../docs/terminology.md#8-the-pipeline)'s only clue to what the entity class or predicate means.

```json
{"entity_classes": [{"component_class": "Instrument", "definition": "A device that takes measurements."},
                    {"component_class": "Spacecraft", "definition": "A craft that operates in space."}],
 "predicates":     [{"component_class": "ABOARD", "definition": "Is carried on."}],
 "patterns":       [{"pattern": ["Instrument", "ABOARD", "Spacecraft"]}]}
```

- `entity_classes` and `predicates` are lists of entries, each with `"component_class"` and `"definition"`.
- `patterns` is a list of `{"pattern": [subject class, predicate, object class]}`; it may be left out.
- `pinned` holds the pins of the text shape's `only:` lines (below), as `schema_used.json` writes them: `{"ACQUIRED_BY_INSTRUMENT": [["Dataset", "Instrument"]]}`; it may be left out.
- Anything else is ignored: 040's `support`, `maintainers`, `texts`, `examples`, `deferred`, `made`. So 040's file works as it is, and so does one written by hand.

**Text (any other ending), like the [ground truth schema](../docs/terminology.md#3-schemas)** `annotations/ground_truth_schema.txt`:

```
ENTITY CLASSES
--------------
Instrument        a device that takes measurements
Spacecraft        a craft that operates in space

PREDICATES
----------
ABOARD            is carried on
                  Instrument -> Spacecraft; Instrument -> Aircraft
```

- An entry is the entity class or predicate (no spaces in it), then **two or more spaces**, then its definition, on one line. If one appears twice, the first entry is kept.
- Under a predicate, an indented line lists its patterns as `Subject -> Object` pairs separated by `;`.
- Under a predicate, an indented line starting `only:` makes it a [pinned predicate](../docs/terminology.md#3-schemas): `only: Dataset -> Instrument; any -> Person` (`any`: any entity class). Its triples may then join only these entity classes, whatever its patterns say; any other pair is flagged `pattern_not_pinned`. The [schema file](../docs/terminology.md#6-extracting-with-a-schema-step-060)'s `only:` lines and the [additions file](../docs/terminology.md#6-extracting-with-a-schema-step-060)'s both apply; one under an entry of the additions file left out because the schema already has it applies to the entry kept, and one under a predicate left out for not coming from [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) is left out with it.
- A pattern can also stand on its own, in a `PATTERNS` section: [subject class](../docs/terminology.md#2-triples), predicate and [object class](../docs/terminology.md#2-triples) on one line, e.g. `Instrument ABOARD Mission`. The additions file uses it to add a pattern to a predicate the schema already has.
- Under any entry (entity class, predicate, or pattern), an indented line starting `source:` says where the idea came from (used by the additions file, and by the [component classes](../docs/terminology.md#3-schemas) and patterns the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) adds to the ground truth schema).
- Lines starting with `#` are comments. Any other line is not read: in a schema given with `--schema` it's ignored as prose (like the explanation in the ground truth schema); in the additions file, where it's usually a mistake, it's pointed out before paying.

So `py 060_extract/run.py --schema annotations/ground_truth_schema.txt` extracts with your ground truth schema.

### Writing the schema additions

Write them in `annotations/schema_additions.txt`, in the text shape above. It holds an example in `#` comments. For instance:

```
ENTITY CLASSES
--------------
Mission           a named spaceflight effort
                  source: mentor

PREDICATES
----------
PART_OF_MISSION   belongs to the mission
                  Spacecraft -> Mission
                  source: mentor

PATTERNS
--------
Instrument ABOARD Mission
                  source: mentor
```

- They're added to whichever [schema](../docs/terminology.md#3-schemas) is used, marked as coming from the [schema additions](../docs/terminology.md#3-schemas), with no [support](../docs/terminology.md#5-learning-the-schema-step-040), [maintainers](../docs/terminology.md#1-records-and-their-text), or [texts](../docs/terminology.md#1-records-and-their-text). A [pattern](../docs/terminology.md#3-schemas) of the `PATTERNS` section adds a pattern to a [predicate](../docs/terminology.md#3-schemas) the schema already has (`ABOARD` above), without repeating the predicate.
- A [schema entry](../docs/terminology.md#3-schemas) of `annotations/schema_additions.txt` that the schema already has is left out, and the schema's entry is kept. So is one that is a loose match for one of the schema's (`spacecraft` or `Space_craft` vs `Spacecraft`), since every [classed triple](../docs/terminology.md#2-triples) the model writes is checked by [loose match](../docs/terminology.md#3-schemas) too (see *component class outside the schema* in the terminology), and so is a second entry of the file repeating an earlier one. Its patterns still apply, to the entry kept.
- Give each one ([entity class](../docs/terminology.md#3-schemas), predicate, or pattern) a `source:` line saying where the **idea** came from (`mentor`, `NASA missions A-to-Z`, …). An entry without one is pointed out before paying.
- **Adding [component classes](../docs/terminology.md#3-schemas) seen in [ground truth](../docs/terminology.md#4-ground-truth-and-samples) [records](../docs/terminology.md#1-records-and-their-text) needs care.** [Step](../docs/terminology.md#8-the-pipeline) 070 evaluates extraction on those records, so one added because it came up there flatters the metrics for exactly those records. Add such component classes only from the **[tuning part](../docs/terminology.md#7-evaluating-extraction-step-070)** (070 shows only its numbers, unless you ask for the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070)), and write `source: ground truth` with the records' [pool](../docs/terminology.md#4-ground-truth-and-samples) positions, as the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) shows them: `source: ground truth tuning #12, #15` (the tool says on each record whether it's tuning or held-out). Code enforces it: a schema entry of `annotations/schema_additions.txt` whose source names the ground truth but doesn't say `tuning`, names a [held-out record](../docs/terminology.md#7-evaluating-extraction-step-070), a position not in the pool, or no record at all is left out, with a note before paying; so are the patterns written under such a predicate. Component classes from outside knowledge, or from a [run](../docs/terminology.md#8-the-pipeline) over every record (the [report](../docs/terminology.md#8-the-pipeline)'s list then leaves the ground truth records out), are fine.

## Outputs

In `outputs/intermediate_results/060_extract/`:

**On a rerun:** every file is replaced, and holds that [run](../docs/terminology.md#8-the-pipeline)'s [records](../docs/terminology.md#1-records-and-their-text) only; `cache/` keeps every answer, so switching back to an earlier [schema](../docs/terminology.md#3-schemas) or set of records costs no [model calls](../docs/terminology.md#8-the-pipeline).

| File | Contents |
|---|---|
| `extracted_triples.csv` | The [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060): for each record extracted, its [describes triple](../docs/terminology.md#2-triples) first, then its [classed triples](../docs/terminology.md#2-triples). Columns `id, subject, subject_class, predicate, object, object_class, source_text, flags, origin`. |
| `extracted_triples_removed.csv` | Every classed triple removed, with `reason` (its values: extracted triple in the terminology; the checks behind them: *How it works*, below); `raw` holds what the [model](../docs/terminology.md#8-the-pipeline) returned when it wasn't a classed triple at all. |
| `schema_used.json` | The [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060), as this run used it: the [schema file](../docs/terminology.md#6-extracting-with-a-schema-step-060) plus the [schema additions](../docs/terminology.md#3-schemas), in the JSON shape above, each entry with `"from": "schema"` or `"additions"` (and its `source`), the pins (`pinned`), the schema entries of `annotations/schema_additions.txt` left out for a clash (`left_out_additions`), and those left out for not coming from [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) only (`left_out_not_tuning`); and which records the schema was learned from (`learned_from`, for finding twins: `070_evaluate/070_evaluate.md`, *Twins*). 070 reads this (and 080 will), so they use exactly what 060 used. |
| `extracted_triples_details.json` | Each record chosen, with its status (`extracted`, or `failed` with the error), [text pieces](../docs/terminology.md#1-records-and-their-text), extracted triples kept and classed triples removed; the records passed over while choosing; and the [component classes](../docs/terminology.md#3-schemas) outside the schema the model used (see the [report](../docs/terminology.md#8-the-pipeline)). |
| `cache/` | Every model answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the [manifest](../docs/terminology.md#8-the-pipeline). |
| `_manifest.json` | [Run id](../docs/terminology.md#8-the-pipeline), [settings](../docs/terminology.md#8-the-pipeline), input files and their hashes, output files and their hashes, headline numbers, and the [harvest](../docs/terminology.md#1-records-and-their-text) date. Written when a run finishes. |

For evaluation: a record **missing** from `extracted_triples.csv` wasn't extracted (a failed call) and must be left out, not evaluated as zero. A record with **only its describes triple** was extracted and states no [fact](../docs/terminology.md#2-triples) the schema can express.

Each run also leaves `outputs/reports/<run id>.md` (the report: what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`. A run in which a model call failed also leaves `outputs/logs/<run id>_failed_calls.jsonl`, the failed-call record: each failed call, why, and what to change (`docs/running_on_nasa_laptop.md`, section 5).

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `extract_from` | ground_truth | `ground_truth`: the [records](../docs/terminology.md#1-records-and-their-text) of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) that are finished (*All facts extracted* ticked), the only ones 070 can evaluate. `all`: every record with [text](../docs/terminology.md#1-records-and-their-text). | `all` once the [schema](../docs/terminology.md#3-schemas) is final. That's about one [model call](../docs/terminology.md#8-the-pipeline) per record, ~36,000; the confirmation shows the number before anything is spent. |
| `ids` | empty | Exactly these records instead: ids separated by commas, or the path of a text file with one id per line (a CSV whose first column is the id works too; a header line `id`, blank lines, and lines starting with `#` are skipped). | To extract from records you choose. |
| `max_chars` | 8000 | A text longer than this is split into [text pieces](../docs/terminology.md#1-records-and-their-text), one model call each (`common/common_helpers/chunking.py`). | Rarely. |
| `workers` | 4 | Model calls made at the same time. | Lower it if the service refuses calls for coming too fast. |
| `service` | litellm | The service that reaches the model: `asksage` (NASA's Ask Sage) or `litellm` (NASA's LiteLLM). Each has its own key in `.env` and its own model names. Every cached answer is tied to its service and model. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `model` | claude-opus-5.5 | The AI [model](../docs/terminology.md#8-the-pipeline) to ask. `py helpers/models.py --service <service>` lists the models the service shows your account; a listed one may still refuse you, which the [run](../docs/terminology.md#8-the-pipeline)'s [test call](../docs/terminology.md#8-the-pipeline) finds out for the price of that call. Every cached answer is tied to its model (and service): another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `thinking` | low | How much a model that thinks before it answers may think: `low`, `medium`, `high`, or `model_default` (nothing sent). Sent only to the models that take it (Gemini 2.5 and later, through LiteLLM); its thinking counts against the longest answer allowed. | When the report's warning says an answer was cut off with most of its tokens spent thinking. See *The thinking cap* in `docs/running_on_nasa_laptop.md`, section 5. |
| `confirm_paid_calls` | true | Stop and ask before the first model call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), on a computer that can reach the model's service and has its key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 060_extract/run.py --help                                  every input and setting, with its default
py 060_extract/run.py                                         the finished ground truth records, with the induced schema
py 060_extract/run.py --schema annotations/ground_truth_schema.txt   with your ground truth schema
py 060_extract/run.py --extract_from all                      every record (once the schema is final)
py 060_extract/run.py --ids 3122be4c-…,cfd6ec3f-…             exactly these records
py 060_extract/run.py --confirm_paid_calls false              don't ask (unattended runs)
```

060 needs 040's `the_schema.json`. Until 040 has run, it stops with *missing input files, so the step can't run: … run `py 040_induce_schema/run.py` first, or give another file with --schema*.

**Paying.** Before its first [model call](../docs/terminology.md#8-the-pipeline), 060 logs its plan (how many [records](../docs/terminology.md#1-records-and-their-text), how many calls, the [model](../docs/terminology.md#8-the-pipeline)) and waits: Enter starts, anything else stops the [run](../docs/terminology.md#8-the-pipeline) having spent nothing. If the run can't do exactly what you asked, it says so first, above the question (*Step 060 found N warnings:*, then each one, numbered; they're listed under *Checks and warnings*). Its first call is the [test call](../docs/terminology.md#8-the-pipeline), which checks that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: one per record, plus one per extra [text](../docs/terminology.md#1-records-and-their-text) piece, plus the test call.

**The cache.** Every model answer is kept in `cache/`, under a [fingerprint](../docs/terminology.md#8-the-pipeline) of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed (but an answer cut off at the length limit is kept as cut off, and not asked again with the same settings: *A cut-off isn't paid for twice* in `docs/running_on_nasa_laptop.md`, section 5). Only an answer of the shape the step reads is kept (a `"triples"` list): one of another shape is asked once more, saying what was wrong, then counts as a failed call; one kept by an earlier version of the code is asked again, and the report's warnings name the cache file (`shape_error` in `common/common_helpers/extraction.py`, `Cache.get` in `common/common_helpers/cache.py`). Editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again.

## How it works

Four [stages](../docs/terminology.md#8-the-pipeline), in `060_extract/run.py`'s `main()`; stage 3 asks the [model](../docs/terminology.md#8-the-pipeline), the others are code:

1. **Pick the [records](../docs/terminology.md#1-records-and-their-text)** (`records.py`, `pick_records`). By `extract_from` or `ids` (above). Anything that differs from what was asked becomes a note shown before paying: a listed id not in the catalog or without [text](../docs/terminology.md#1-records-and-their-text), [ground truth](../docs/terminology.md#4-ground-truth-and-samples) records not yet finished.
2. **Load the [schema](../docs/terminology.md#3-schemas)** (`schema.py`, `load_schema`). The [schema file](../docs/terminology.md#6-extracting-with-a-schema-step-060) (the file given with `--schema`, the [induced schema](../docs/terminology.md#5-learning-the-schema-step-040) by default) plus the [schema additions](../docs/terminology.md#3-schemas), merged into the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060), each entry remembering where it came from. Notes: schema entries of `annotations/schema_additions.txt` from the ground truth that don't name [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070) only (left out), entries of the schema file whose `source:` line fails the same check (kept), entries of the schema additions that clash with the schema, entries of the schema additions with no `source:` line, schema entries with no definition, [entity classes](../docs/terminology.md#3-schemas) or [predicates](../docs/terminology.md#3-schemas) in [patterns](../docs/terminology.md#3-schemas) or `only:` lines that the schema doesn't have.
3. **Ask the model** (`extract.py`, `ask_model`). One call per [text piece](../docs/terminology.md#1-records-and-their-text), with the prompt `060_extract/060_extract_prompts/extract.txt`: extract only the [facts](../docs/terminology.md#2-triples) the schema can express, with only the schema's [component classes](../docs/terminology.md#3-schemas), and name the [describes class](../docs/terminology.md#2-triples) (`describes_class`), or none if no entity class fits. The model sees the schema in the text shape above. The rules and the reply format are 050's (`common/common_prompts/`), so what 060 extracts and what 050 drafts are asked for the same way. The calls are made by `common/common_helpers/extraction.py`, as in 050: every answer is cached the moment it arrives, and a record with a failed call is left out whole, never half extracted.
4. **Check and sort the [classed triples](../docs/terminology.md#2-triples)** (`extract.py`, `sort_rows`). `common/common_helpers/extraction.py` builds each record's classed triples (the [describes triple](../docs/terminology.md#2-triples) first) and checks every one against the record's **whole** text and the schema (`common/common_helpers/validate.py`). Then:

   | What | Where it goes | Why |
   |---|---|---|
   | Its [source text](../docs/terminology.md#1-records-and-their-text) is missing, or isn't in the record's text | **removed**, reason `source_text` | It can't be verified, and may be invented. |
   | An entity class or predicate the schema doesn't have | **removed**, reason `component_class_not_in_schema` | The graph can only hold the schema's component classes, and the prompt allows no others. The [report](../docs/terminology.md#8-the-pipeline) lists these component classes (below). One that is a [loose match](../docs/terminology.md#3-schemas) for one of the schema's is not outside the schema: it's accepted and written in the schema's spelling. |
   | [The same classed triple twice](../docs/terminology.md#4-ground-truth-and-samples) | **removed**, reason `duplicate` | Counted once. |
   | Something that isn't a classed triple at all | **removed**, reason `malformed` | Nothing to keep. |
   | A pattern the schema doesn't list (known component classes, new combination) | **kept**, [flag](../docs/terminology.md#2-triples) `pattern_not_in_schema` | The schema's patterns are what was seen, not all that's allowed. |
   | A [pinned predicate](../docs/terminology.md#3-schemas) with a [subject class](../docs/terminology.md#2-triples) and [object class](../docs/terminology.md#2-triples) its `only:` line doesn't list | **kept**, flag `pattern_not_pinned` | Worth a look: the pin says what the predicate may join. |
   | Any other flag (a reworded subject or [object instance](../docs/terminology.md#2-triples), subject instance equal to object instance, the same [subject instance](../docs/terminology.md#2-triples), predicate, and object instance with other entity classes) | **kept**, flagged | Often fine; worth a look. |
   | The describes triple | **always kept** | Every record extracted has one. If the model named no entity class for it, or one the schema doesn't have, its entity class is `X`, flagged `describes_undecided`. |

The flag names are listed in `050_annotate/050_annotate.md` (*Checks on each row*).

**Component classes outside the schema.** The report's table *Component classes outside the schema* lists the entity classes and predicates the model used that the current schema doesn't have, most used first, each with the `source:` line its entry in `annotations/schema_additions.txt` needs. Only component classes it is fair to add are counted: **[held-out records](../docs/terminology.md#7-evaluating-extraction-step-070) are never counted** (one learned there would let held-out records influence the schema, and the held-out numbers would no longer measure records the pipeline was never adjusted to); tuning records are, and are named by [pool](../docs/terminology.md#4-ground-truth-and-samples) position (`source: ground truth tuning #0, #12`); on a [run](../docs/terminology.md#8-the-pipeline) over every record, no ground truth record is counted at all (`source: extraction over records not annotated`). The full list is in `extracted_triples_details.json`, under `new_component_classes`.

**Then the results** (`results`): the four files are written, replacing the last run's (whose versions are kept in `previous_runs/<run id>/` when they differ: `helpers/audit.md`, *Where to look*); the report. Its subsection *Extracted triples* (section *Results*) starts with a table, *Classed triples per text*: for each text (one record's text), how many classed triples the model listed (row *raw*: kept + removed by a check, with the reason `source_text` or `component_class_not_in_schema`) and how many were kept (row *kept (extracted triples)*), describes triples not counted, given as the number of texts, min, max, mean, median, total, and texts with none. A classed triple two text pieces of a text both state counts once (a repeat is removed as `duplicate`); items that weren't [triple instances](../docs/terminology.md#2-triples) (removed as `malformed`), and texts whose [model call](../docs/terminology.md#8-the-pipeline) failed, aren't counted. The headline, and `_manifest.json`, also give both totals and their means per text (`raw classed triples`, `extracted triples`).

The code: `060_extract/` holds `run.py` (the [control panel](../docs/terminology.md#8-the-pipeline): inputs, [settings](../docs/terminology.md#8-the-pipeline), and the [moves](../docs/terminology.md#8-the-pipeline), in order); `060_extract/060_extract_helpers/` holds `moves.py` (the moves, and writing the results), `records.py`, `schema.py` and `extract.py`; `060_extract/060_extract_prompts/` holds the prompts (see *Prompts*). Shared with other [steps](../docs/terminology.md#8-the-pipeline): `common/common_helpers/extraction.py` and `common/common_prompts/` (asking the model and building rows, with 050), `common/common_helpers/schema_io.py` (reading schemas), `common/common_helpers/validate.py` (the checks), `common/common_helpers/cache.py`, `common/common_helpers/llm.py`.

### The schema in the prompt: what the literature does, and why 060 does this

060 shows the model the whole schema in every request: each [entity class](../docs/terminology.md#3-schemas) and predicate with its definition, and every pattern. For the [induced schema](../docs/terminology.md#5-learning-the-schema-step-040) of the baseline run of 2026-10-12 that is about 58,000 characters, roughly 14,500 tokens (about 4 characters each, not counted exactly): entity classes 15%, predicates 27%, patterns 58%. It is the same in every request, so it matters most for the run on the whole catalog (about 36,000 requests). What published work does (read on 2026-10-12):

- **The whole schema in the prompt**, as 060 does: the usual design for small schemas. Text2KGBench (Mihindukulasooriya et al. 2023, §5.2) lists the ontology's entity classes, and each predicate with its domain and range, e.g. "director(film, human)"; its ontologies have at most 68 predicates, and its authors note that "much larger ontologies … will require systems to automatically select the portion of the ontology … relevant to the given input text" (§7).
- **Only the relevant part of the schema for each text.** EDC (Zhang & Soh 2024) extracts with no schema, then maps each [predicate instance](../docs/terminology.md#2-triples) it extracted to the most similar predicates of the schema (top 5, then a trained retriever's top 10), because "larger and more complex schemas easily exceed the LLMs' context window length". SchemaRAG (Ho et al. 2026) found a retrieved subset more accurate than the full schema on two extraction tasks (micro-F1 0.918 vs 0.844, 0.510 vs 0.471) at lower cost. Both measured older models (GPT-3.5, GPT-4o) and other tasks; no study measures schema length against quality with current models, and 14,500 tokens is far inside today's context windows.
- **Patterns (domain and range)** are given in the prompt in some work (Text2KGBench) and only checked afterwards in other work (EDC); no study compares the two.

**Why 060 keeps the whole schema for now.** It is the simplest design, and the baseline. Two changes are experiments, each compared with the baseline on the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) (`helpers/compare_runs.md`): leaving the patterns out of the prompt (060 still checks them afterwards), and, only if that shows a long schema hurts, giving each record the relevant part of the schema.

**Prompt caching, for cost.** Anthropic's API can keep an identical start of a prompt in a cache: a later request starting the same way pays 5% of the normal input price for that part (Claude Opus 5.5), while writing it to the cache costs 1.25 times. The schema, identical in every request, is such a start. Through NASA's LiteLLM it works: in a test on 2026-10-12, 4 of 8 identical requests read the cache, and the pattern (writes, then reads) fits several copies of the model behind the service, each writing its cache once (`docs/findings.md`). Caching pays once about 1 request in 5 reads. So 060 sends everything before the record's text (the instructions, the schema, the rules: the same in every request) as a block marked for caching, and the record as the rest, for Anthropic's models only (code: `_messages` in `common/common_helpers/llm.py`); the model gets the same words either way. Each report's *Model calls* counts the tokens read from and written to the cache. 040 and 050 don't ask for caching: 040's runs should send their messages as the baseline run did, and 050 uses a Gemini model, whose caching works differently.

**Batch requests** (half price, answers within a day) exist for Anthropic's models, but whether NASA's LiteLLM offers them isn't known; its administrators would know.

## Prompts

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `060_extract/060_extract_prompts/extract.txt` | [stage](../docs/terminology.md#8-the-pipeline) 3, one call per [text piece](../docs/terminology.md#1-records-and-their-text) | list only the [facts](../docs/terminology.md#2-triples) the [schema](../docs/terminology.md#3-schemas) can express, using **only** the schema's [entity classes](../docs/terminology.md#3-schemas) and [predicates](../docs/terminology.md#3-schemas) (the schema is shown in the prompt), and name the [describes class](../docs/terminology.md#2-triples), or none if no entity class fits |
| `common/common_prompts/extraction_rules.txt` | inside `extract.txt` (`$rules`) | follow the rules shared with 040 and 050, the model's copy of the [annotation guidelines](../docs/terminology.md#4-ground-truth-and-samples): what counts as a fact and how to write a [classed triple](../docs/terminology.md#2-triples). The rules themselves: `annotations/guidelines.md` (the model's copy: this file; a test keeps the two in step) |
| `common/common_prompts/extraction_reply.txt` | inside `extract.txt` (`$reply`) | reply in the JSON form shared with 040 and 050, each classed triple with its entity classes |

Each prompt is a plain text file: open it to read exactly what the [model](../docs/terminology.md#8-the-pipeline) is told. `$name` marks where the code fills something in. The prompts speak plainly to the model ("facts", "entity classes", "predicates"), explaining any term they use. Editing a prompt is allowed: the next [run](../docs/terminology.md#8-the-pipeline) asks again every call that uses it, and pays for them. The two `common/common_prompts/` files are shared with 050: editing them changes both [steps](../docs/terminology.md#8-the-pipeline). The examples in `extraction_rules.txt` are invented, never text from a [ground truth](../docs/terminology.md#4-ground-truth-and-samples) record, so the prompt can't hand the model an answer it is scored on; `tests/test_docs.py` checks it.

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the [report](../docs/terminology.md#8-the-pipeline)'s warnings):

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) of the ground truth aren't finished yet … so skipped* | Only [finished records](../docs/terminology.md#4-ground-truth-and-samples) can be evaluated. | Finish them in `py helpers/annotate.py`, or ignore. |
| *Ground truth, record … is in batch_… and batch_…: annotated twice* | A [record](../docs/terminology.md#1-records-and-their-text) is annotated twice. It's left out of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) until fixed. | Keep it in one file. |
| *Ground truth, record … (batch_…): all_facts_extracted is 0 on some rows, 1 on others* | Mixed, so the record doesn't count as finished. | Set it the same on every row (the tool's box does). |
| *Ground truth, record … (batch_…): lines … and … are the same classed triple.*, then each line | [The same classed triple twice](../docs/terminology.md#4-ground-truth-and-samples) in one record (a hand edit). Only one copy can be paired, so evaluation would count the other as ground truth only. Step 070 refuses to run until one is deleted. | Delete one of the two rows. |
| *Ground truth, record … (batch_…): lines … and … state the same subject instance, predicate, and object instance, with different entity classes.*, then each line | Likely one fact given two [entity classes](../docs/terminology.md#3-schemas) by mistake. | If they state one fact, delete the line with the wrong entity classes. |
| *The ground truth of N of the records chosen was drafted (step 050) by …, the same model as this run's (…) / a model from the same maker (…) as this run's …* | Shown before paying. Facts that model misses tend to be missing from both the ground truth and the extraction, so recall would look better than it is (see `070_evaluate/metrics/recall.md`). The maker is read from the model's name (`common/common_helpers/llm.py`, `maker`); a model whose name the table doesn't know is compared by name only. | Rerun with `--model` naming a model from another maker (`py helpers/models.py` lists them), or go ahead for a test run. |
| *Ground truth, batch_… lacks the column(s) …; not read* | A ground truth file without one of the columns (see `annotations/README.md`). | Add the column. |
| *N record(s) you listed is/are not in the catalog / without text, so skipped* | With `ids`. | Check for typos. |
| *N ground truth record(s) is/are not in the catalog / without text, so skipped* | With `extract_from` = `ground_truth` (the default): a ground truth id that isn't in 020's records, or a record with no [text](../docs/terminology.md#1-records-and-their-text) to read. | Check the id in `annotations/ground_truth/` for typos; a record without text can't be extracted. |
| *extract_from (…) is ignored, because the setting ids names the records* | Both were given. | Nothing to do if you meant the ids; to extract from the records `extract_from` names instead, leave `ids` empty. |
| *N schema entr(ies) of … are already there (in the schema file, or earlier in the same file, ignoring case and punctuation), so each is left out and the entry already there is used* | A clash, by [loose match](../docs/terminology.md#3-schemas). | Remove or rename the entry. |
| *N line(s) of schema_additions.txt aren't read as an entry, a source, or patterns …* | The first 5 are listed with their line numbers: usually an entity class or predicate with a space in it, one space before the definition, a [pattern](../docs/terminology.md#3-schemas) line not in the `Subject -> Object; …` form, or a repeated entry (the first is kept; the repeat and the lines under it are listed). Such a line adds nothing. | Fix the line (see *The shape of a schema*). |
| *N schema entr(ies) of … say they come from the ground truth but don't show they come from tuning records only, so they are left out* | Each is listed with why: it doesn't say `tuning`, or names a [held-out record](../docs/terminology.md#7-evaluating-extraction-step-070), a position not in the [pool](../docs/terminology.md#4-ground-truth-and-samples), or no record. | Take the entry out, or (if it really came from [tuning records](../docs/terminology.md#7-evaluating-extraction-step-070)) list their [pool positions](../docs/terminology.md#4-ground-truth-and-samples): `source: ground truth tuning #12`. |
| *Entries of … whose source names ground truth records other than tuning ones (N)* | The [schema](../docs/terminology.md#3-schemas) given with `--schema` (e.g. the [ground truth schema](../docs/terminology.md#3-schemas)) has entries whose `source:` line names the ground truth but fails the check entries of the [schema additions](../docs/terminology.md#3-schemas) get: it names a held-out record, doesn't say `tuning`, names a position not in the pool, or names no record. Usually [component classes](../docs/terminology.md#3-schemas) or patterns learned from held-out records: the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) gives each one it adds there a `source:` line naming the records that use it. They are kept. | Fine for tuning numbers. Don't trust this [run](../docs/terminology.md#8-the-pipeline)'s held-out numbers: extract with a schema that didn't learn from held-out records (040's, by default). |
| *N schema entr(ies) of … have no "source:" line …* | Where the idea came from isn't recorded. | Add a `source:` line under each. |
| *N schema entries have no definition …* | The [model](../docs/terminology.md#8-the-pipeline) will see those entity classes or predicates with no definition. | Add definitions. |
| *N component class(es) used in patterns or "only:" lines aren't in the schema* | A pattern or an `only:` line uses something the schema doesn't have (often a typo). | Fix the pattern or line, or add the missing entity class or predicate. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) failed: a model call for one of their text pieces failed, so each is left out of the output whole* | A [model call](../docs/terminology.md#8-the-pipeline) for a [text piece](../docs/terminology.md#1-records-and-their-text) of those records failed (after the model client's own retries), so each is left out whole, never half extracted. The report gives each record's id and why. | Run the step again: only the failed pieces are asked again, and every answer already paid for is reused. An answer cut off at the length limit isn't asked again with the same settings: first change the setting the warning names (`docs/running_on_nasa_laptop.md`, section 7). Each failed call is described in `outputs/logs/<run id>_failed_calls.jsonl`. |
| *N of M rows have no origin, so they can't be traced to the input they came from* | Should never happen: a code change dropped the field that records where each item came from. | Fix the code before using the output. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *missing input files, so the step can't run: … schema … run `py 040_induce_schema/run.py` first, or give another file with --schema* | 040 hasn't run. | Run 040 (or pass `--schema`). |
| *… has no entity classes or no predicates (…), so 060 can't extract with it* | The `--schema` file isn't in either shape. | Check the file against *The shape of a schema* (Inputs). |
| *… a JSON schema must be an object with entity_classes and predicates* / *"entity_classes" must be a list …* / *… entry N has no "component_class"* / *patterns entry N must be …* / *"pinned" must be an object …* / *pinned entry … must be a list of [subject class, object class]* | A JSON schema that doesn't follow the shape above. | Fix the file (see *The shape of a schema*). |
| *extract_from must be one of ground_truth, all* | A typo in the [setting](../docs/terminology.md#8-the-pipeline). | Use `ground_truth` or `all`. |
| *No ground truth files at …, so 060 has no finished records to extract from (extract_from is ground_truth)* | No record is annotated yet. | Annotate records first (`py 050_annotate/run.py`, then `py helpers/annotate.py`), or give `--extract_from all`, or name the records with `--ids`. |
| *Nothing to extract: none of the records chosen can be extracted from …* | No record could be chosen; the reasons follow. | Change the settings: the reasons are listed. |
| *… must be at least N* | A setting is out of range: `workers` under 1, or `max_chars` under 1,000. | Fix the setting. |
| *The setting model is empty …*, *The setting service is …*, *The setting thinking is …*, *Test call to … failed*, *Test call to … was cut off …*, *The test call's one-line answer used N tokens thinking …*, *Step NNN stopped early: …*, *… isn't set, so no model can be called*, *Cancelled. Nothing was spent.*, *Stopped with Ctrl+C. …* | The stops (and the [test call](../docs/terminology.md#8-the-pipeline)'s warning) every step that calls the model shares. | `docs/running_on_nasa_laptop.md`, section 7, says what each means and what to do. |

## Audit trail

- **Prompts.** The [report](../docs/terminology.md#8-the-pipeline)'s *Prompts* section lists every prompt the [run](../docs/terminology.md#8-the-pipeline) filled in, each with a [fingerprint](../docs/terminology.md#8-the-pipeline) (sha256) of its exact text, so the prompt behind any answer is known even if the prompt file was edited later (`_manifest.json` keeps the full fingerprints).
- **[Log](../docs/terminology.md#8-the-pipeline).** `outputs/logs/<run id>.log` records the command line, the [settings](../docs/terminology.md#8-the-pipeline), the git commit, every [model call](../docs/terminology.md#8-the-pipeline)'s retries, each [move](../docs/terminology.md#8-the-pipeline)'s duration, each output file's hash and, on failure, the full traceback.
- **[Origin](../docs/terminology.md#8-the-pipeline).** Each [extracted triple](../docs/terminology.md#6-extracting-with-a-schema-step-060) and each removed [classed triple](../docs/terminology.md#2-triples) has an `origin` column naming its [record](../docs/terminology.md#1-records-and-their-text) in 020's `records.jsonl`; `schema_used.json` names the [schema](../docs/terminology.md#3-schemas) file and [additions file](../docs/terminology.md#6-extracting-with-a-schema-step-060) it was built from.
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every [step](../docs/terminology.md#8-the-pipeline)'s output to the 010 [batch file](../docs/terminology.md#1-records-and-their-text) and the API request that first returned it (`helpers/audit.md`).

## Known limits

- **Tested with a stand-in model before its first real run.** As of 2026-09-29, 060 had been tested only with a [stand-in model](../docs/terminology.md#8-the-pipeline), and with an induced [schema](../docs/terminology.md#3-schemas) from a stand-in-model [run](../docs/terminology.md#8-the-pipeline), because the model's services can't be reached from the laptop it was built on. Numbers in this guide come from the catalog, the code, or the stand-in, not from a real run. Since 2026-10-12, the model's service is reached from the NASA laptop, where step 040 made, with the real model, the schema that 060 and 070 start from ([`findings.md`](../docs/findings.md#2026-10-12--step-040--the-baseline-schema)); 060 first ran with the real model there by 2026-10-22: 070 run 2026-10-22_1615 evaluated its output. That run isn't recorded in `findings.md` yet.
- **[Patterns](../docs/terminology.md#3-schemas) are not enforced.** A [classed triple](../docs/terminology.md#2-triples) joining two known [entity classes](../docs/terminology.md#3-schemas) with a known [predicate](../docs/terminology.md#3-schemas) is kept even if the schema has no such pattern. 070's metrics will show whether that lets in wrong [facts](../docs/terminology.md#2-triples).
- **A synonym is removed, not repaired.** A [component class](../docs/terminology.md#3-schemas) spelled differently (`Space craft`, `SPACECRAFT` for `Spacecraft`) is accepted, since component classes are compared by [loose match](../docs/terminology.md#3-schemas), and it is written in the schema's own spelling. A true synonym (`Satellite`) is removed; the [report](../docs/terminology.md#8-the-pipeline) lists it.
- **The model varies.** Rerunning with an empty cache can extract different classed triples; the cache makes a rerun reproducible.
