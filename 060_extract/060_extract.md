# 060_extract

Terms ([classed triple](../docs/terminology.md#2-triples), [entity class](../docs/terminology.md#3-schemas), [schema](../docs/terminology.md#3-schemas), [pattern](../docs/terminology.md#3-schemas), [DESCRIBES row](../docs/terminology.md#2-triples), [error](../docs/terminology.md#2-triples), [flag](../docs/terminology.md#2-triples), [schema additions](../docs/terminology.md#3-schemas), …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Extracting with a schema (step 060)*.

## Purpose

Extracts, from each [record](../docs/terminology.md#1-records-and-their-text)'s [text](../docs/terminology.md#1-records-and-their-text), the [facts](../docs/terminology.md#2-triples) a [schema](../docs/terminology.md#3-schemas) can express. A [model](../docs/terminology.md#8-the-pipeline) lists them as [classed triples](../docs/terminology.md#2-triples) using **only** the schema's [entity classes](../docs/terminology.md#3-schemas) and [predicates](../docs/terminology.md#3-schemas). Code checks every one against the record's text and the schema, then keeps it or removes it with a reason. What 060 keeps is what [step](../docs/terminology.md#8-the-pipeline) 070 evaluates against the [ground truth](../docs/terminology.md#4-ground-truth-and-samples), and what step 080 will build the graph from.

The schema is 040's [induced schema](../docs/terminology.md#5-learning-the-schema-step-040) by default, plus the entity classes, predicates and [patterns](../docs/terminology.md#3-schemas) you add by hand in `annotations/schema_additions.txt` (e.g. on a mentor's advice). By default, 060 extracts only from the records of the ground truth you've finished, the ones 070 can evaluate. Once the schema is final, `--extract_from all` extracts from every record.

## To do

### Every step

The same for every [step](../docs/terminology.md#8-the-pipeline): see [*Every step* in step 010's guide](../010_harvest/010_harvest.md#every-step).

### This step

#### Before running

- **Before the real [runs](../docs/terminology.md#8-the-pipeline), choose the [model](../docs/terminology.md#8-the-pipeline):** from a different maker than annotation's, so the two don't share blind spots; for the run over every [record](../docs/terminology.md#1-records-and-their-text), the cheapest whose metrics are within the [margin of error](../docs/terminology.md#7-evaluating-extraction-step-070) of the best (`docs/running_on_nasa_laptop.md`, *Choosing a model*).
- **Rerun it after finishing more [ground truth](../docs/terminology.md#4-ground-truth-and-samples) records:** by default it extracts only the finished ones, and evaluation can evaluate only what it extracted.

#### After running

- **Read the [report](../docs/terminology.md#8-the-pipeline)'s table *[Component classes](../docs/terminology.md#3-schemas) outside the [schema](../docs/terminology.md#3-schemas)*** (`outputs/reports/060_extract_<date>_<time>.md`): [entity classes](../docs/terminology.md#3-schemas) and [predicates](../docs/terminology.md#3-schemas) the model used that the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) doesn't have, from tuning records and records outside the ground truth only (never held-out ones). For one that keeps coming back and names a real kind of thing or relation, add it to `annotations/schema_additions.txt` (easiest: `py helpers/annotate.py`, *Schema additions*, where each listed component class has an *Add* button) with a one-line definition and the `source:` line the table gives (e.g. `source: ground truth tuning #0, #12`). Every component class listed is fair to add.
- **Give every addition in `annotations/schema_additions.txt` a `source:` line.** A component class learned from the ground truth must come from tuning records only, named by [pool](../docs/terminology.md#4-ground-truth-and-samples) position (`source: ground truth tuning #12`); the [step](../docs/terminology.md#8-the-pipeline) leaves out any other.
- **Now and then, read the removed [classed triples](../docs/terminology.md#2-triples)** (`outputs/intermediate_results/060_extract/extracted_triples_removed.csv`, each with its reason). A rule that removes good [facts](../docs/terminology.md#2-triples) is a sign the schema, or the prompt, needs work.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned [records](../docs/terminology.md#1-records-and-their-text): the [texts](../docs/terminology.md#1-records-and-their-text). |
| `splits` | `030_split/splits.json` | Which [pool](../docs/terminology.md#4-ground-truth-and-samples) records are tuning and which held-out: an addition learned from the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) is used only if it names tuning records. |
| `schema` | `040_induce_schema/the_schema.json` | The [schema](../docs/terminology.md#3-schemas) to extract with. Any schema in one of the two shapes below can be given instead: `--schema <file>`. |
| `additions` | `./annotations/schema_additions.txt` (in Git) | [Entity classes](../docs/terminology.md#3-schemas) and [predicates](../docs/terminology.md#3-schemas) added by hand to whichever schema is used. Starts empty. |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | Which records have ground truth, and which are finished. |

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
- Anything else is ignored: 040's `support`, `maintainers`, `texts`, `examples`, `deferred`, `made`. So 040's file works as it is, and so does one written by hand.

**Text (any other ending), like the [hand-built schema](../docs/terminology.md#3-schemas)** `annotations/schema_derived_from_manual_annotation.txt`:

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
- A pattern can also stand on its own, in a `PATTERNS` section: [subject class](../docs/terminology.md#2-triples), predicate and [object class](../docs/terminology.md#2-triples) on one line, e.g. `Instrument ABOARD Mission`. The additions file uses it to add a pattern to a predicate the schema already has.
- Under any entry (entity class, predicate or pattern), an indented line starting `source:` says where the idea came from (used by the additions file, and by the [component classes](../docs/terminology.md#3-schemas) the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) adds to the hand-built schema).
- Lines starting with `#` are comments. Any other line is not read: in a schema given with `--schema` it's ignored as prose (like the explanation in the hand-built schema); in the additions file, where it's usually a mistake, it's pointed out before paying.

So `py 060_extract/run.py --schema annotations/schema_derived_from_manual_annotation.txt` extracts with your hand-built schema.

### Adding entity classes, predicates and patterns by hand

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

- They're added to whichever [schema](../docs/terminology.md#3-schemas) is used, marked as coming from the additions, with no [support](../docs/terminology.md#5-learning-the-schema-step-040), [maintainers](../docs/terminology.md#1-records-and-their-text) or [texts](../docs/terminology.md#1-records-and-their-text). A [pattern](../docs/terminology.md#3-schemas) of the `PATTERNS` section adds a pattern to a [predicate](../docs/terminology.md#3-schemas) the schema already has (`ABOARD` above), without repeating the predicate.
- An addition the schema already has is left out, and the schema's entry is kept. So is one differing only in case or punctuation (`spacecraft` or `Space_craft` vs `Spacecraft`), since every row is checked by [loose match](../docs/terminology.md#3-schemas) too (see *component class outside the schema* in the terminology), and so is a second addition repeating an earlier one. Its patterns still apply, to the entry kept.
- Give each one ([entity class](../docs/terminology.md#3-schemas), predicate or pattern) a `source:` line saying where the **idea** came from (`mentor`, `NASA missions A-to-Z`, …). An addition without one is pointed out before paying.
- **Adding [component classes](../docs/terminology.md#3-schemas) seen in [ground truth](../docs/terminology.md#4-ground-truth-and-samples) [records](../docs/terminology.md#1-records-and-their-text) needs care.** [Step](../docs/terminology.md#8-the-pipeline) 070 evaluates extraction on those records, so one added because it came up there flatters the metrics for exactly those records. Add such component classes only from the **[tuning part](../docs/terminology.md#7-evaluating-extraction-step-070)** (070 shows only its numbers, unless you ask for the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070)), and write `source: ground truth` with the records' [pool](../docs/terminology.md#4-ground-truth-and-samples) positions, as the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) shows them: `source: ground truth tuning #12, #15` (the tool says on each record whether it's tuning or held-out). Code enforces it: an addition whose source mentions the ground truth but doesn't say `tuning`, names a held-out record, a position not in the pool, or no record at all is left out, with a note before paying; so are the patterns written under such a predicate. Component classes from outside knowledge, or from a [run](../docs/terminology.md#8-the-pipeline) over every record (the [report](../docs/terminology.md#8-the-pipeline)'s list then leaves the ground truth records out), are fine.

## Outputs

In `outputs/intermediate_results/060_extract/`:

**On a rerun:** every file is replaced, and holds that [run](../docs/terminology.md#8-the-pipeline)'s [records](../docs/terminology.md#1-records-and-their-text) only; `cache/` keeps every answer, so switching back to an earlier [schema](../docs/terminology.md#3-schemas) or set of records costs no [model calls](../docs/terminology.md#8-the-pipeline).

| File | Contents |
|---|---|
| `extracted_triples.csv` | The [extracted triples](../docs/terminology.md#6-extracting-with-a-schema-step-060): for each record extracted, its [DESCRIBES row](../docs/terminology.md#2-triples) first, then its [classed triples](../docs/terminology.md#2-triples). Columns `id, subject, subject_class, predicate, object, object_class, source_text, flags, origin`. |
| `extracted_triples_removed.csv` | Every classed triple removed, with `reason` (below; both, if both apply); `raw` holds what the [model](../docs/terminology.md#8-the-pipeline) returned when it wasn't a classed triple at all. |
| `schema_used.json` | The schema this run used: the schema input plus the additions, in the JSON shape above, each entry with `"from": "schema"` or `"additions"` (and its `source`), the additions left out for a clash (`left_out_additions`), and those left out for not coming from tuning records only (`left_out_not_tuning`). 070 reads this (and 080 will), so they use exactly what 060 used. |
| `extracted_triples_details.json` | Each record chosen, with its status (`extracted`, or `failed` with the error), [text pieces](../docs/terminology.md#1-records-and-their-text), rows kept and removed; the records passed over while choosing; and the [component classes](../docs/terminology.md#3-schemas) outside the schema the model used (see the [report](../docs/terminology.md#8-the-pipeline)). |
| `cache/` | Every model answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the [manifest](../docs/terminology.md#8-the-pipeline). |
| `_manifest.json` | [Run id](../docs/terminology.md#8-the-pipeline), [settings](../docs/terminology.md#8-the-pipeline), input files and their hashes, output files and their hashes, headline numbers and the [harvest](../docs/terminology.md#1-records-and-their-text) date. Written when a run finishes. |

For evaluation: a record **missing** from `extracted_triples.csv` wasn't extracted (a failed call) and must be left out, not evaluated as zero. A record with **only its DESCRIBES row** was extracted and states no [fact](../docs/terminology.md#2-triples) the schema can express.

Each run also leaves `outputs/reports/<run id>.md` (the report: what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `extract_from` | ground_truth | `ground_truth`: the [records](../docs/terminology.md#1-records-and-their-text) of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) that are finished (*All facts extracted* ticked), the only ones 070 can evaluate. `all`: every record with [text](../docs/terminology.md#1-records-and-their-text). | `all` once the [schema](../docs/terminology.md#3-schemas) is final. That's about one [model call](../docs/terminology.md#8-the-pipeline) per record, ~36,000; the confirmation shows the number before anything is spent. |
| `ids` | empty | Exactly these records instead: ids separated by commas, or the path of a text file with one id per line (a CSV whose first column is the id works too; a header line `id`, blank lines and lines starting with `#` are skipped). | To extract from records you choose. |
| `max_chars` | 8000 | A text longer than this is split into [text pieces](../docs/terminology.md#1-records-and-their-text), one model call each (`common/common_helpers/chunking.py`). | Rarely. |
| `workers` | 4 | Model calls made at the same time. | Lower it if Ask Sage refuses calls for coming too fast. |
| `model` | google-claude-sonnet-5 | The AI [model](../docs/terminology.md#8-the-pipeline) to ask. `py helpers/models.py` lists the models Ask Sage shows your account; a listed one may still refuse you, which the [run](../docs/terminology.md#8-the-pipeline)'s first call (the one-line test) finds out for the price of that call. Every cached answer is tied to its model: another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `confirm_paid_calls` | true | Stop and ask before the first model call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), on a computer that can reach Ask Sage and has your key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 060_extract/run.py --help                                  every input and setting, with its default
py 060_extract/run.py                                         the finished ground truth records, with 040's schema
py 060_extract/run.py --schema annotations/schema_derived_from_manual_annotation.txt   with your hand-built schema
py 060_extract/run.py --extract_from all                      every record (once the schema is final)
py 060_extract/run.py --ids 3122be4c-…,cfd6ec3f-…             exactly these records
py 060_extract/run.py --confirm_paid_calls false              don't ask (unattended runs)
```

060 needs 040's `the_schema.json`. Until 040 has run, it stops with *missing input files … run 040_induce_schema first, or pass --schema*.

**Paying.** Before its first [model call](../docs/terminology.md#8-the-pipeline), 060 logs its plan (how many [records](../docs/terminology.md#1-records-and-their-text), how many calls, the [model](../docs/terminology.md#8-the-pipeline)) and waits: Enter starts, anything else stops the [run](../docs/terminology.md#8-the-pipeline) having spent nothing. If the run can't do exactly what you asked, it says so first, above the question (*Step 060 found N warnings:*, then each one, numbered; they're listed under *Checks and warnings*). Its first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: one per record, plus one per extra piece of a long [text](../docs/terminology.md#1-records-and-their-text), plus the test call.

**The cache.** Every model answer is kept in `cache/`, under a [fingerprint](../docs/terminology.md#8-the-pipeline) of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed; editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again.

## How it works

Four [stages](../docs/terminology.md#8-the-pipeline), in `060_extract/run.py`'s `main()`; stage 3 asks the [model](../docs/terminology.md#8-the-pipeline), the others are code:

1. **Pick the [records](../docs/terminology.md#1-records-and-their-text)** (`records.py`, `pick_records`). By `extract_from` or `ids` (above). Anything that differs from what was asked becomes a note shown before paying: a listed id not in the catalog or without [text](../docs/terminology.md#1-records-and-their-text), [ground truth](../docs/terminology.md#4-ground-truth-and-samples) records not yet finished.
2. **Load the [schema](../docs/terminology.md#3-schemas)** (`schema.py`, `load_schema`). The schema input plus the additions, merged, each entry remembering where it came from. Notes: additions from the ground truth that don't name tuning records only (left out), entries of the schema input whose `source:` line fails the same check (kept), additions that clash with the schema, additions with no `source:` line, entries with no definition, [entity classes](../docs/terminology.md#3-schemas) or [predicates](../docs/terminology.md#3-schemas) in [patterns](../docs/terminology.md#3-schemas) that the schema doesn't have.
3. **Ask the model** (`extract.py`, `ask_model`). One call per [text piece](../docs/terminology.md#1-records-and-their-text), with the prompt `060_extract/060_extract_prompts/extract.txt`: extract only the [facts](../docs/terminology.md#2-triples) the schema can express, with only the schema's [component classes](../docs/terminology.md#3-schemas), and name the entity class of what the title names (`describes_class`), or none if no entity class fits. The model sees the schema in the text shape above. The rules and the reply format are 050's (`common/common_prompts/`), so what 060 extracts and the ground truth 050 drafted are asked for the same way. The calls are made by `common/common_helpers/extraction.py`, as in 050: every answer is cached the moment it arrives, and a record with a failed call is left out whole, never half extracted.
4. **Check and sort the rows** (`extract.py`, `sort_rows`). `common/common_helpers/extraction.py` builds each record's rows (the [DESCRIBES row](../docs/terminology.md#2-triples) first) and checks every one against the record's **whole** text and the schema (`common/common_helpers/validate.py`). Then:

   | What | Where it goes | Why |
   |---|---|---|
   | Its [source text](../docs/terminology.md#1-records-and-their-text) is missing, or isn't in the record's text | **removed**, reason `source_text` | It can't be verified, and may be invented. |
   | An entity class or predicate the schema doesn't have | **removed**, reason `component_class_not_in_schema` | The graph can only hold the schema's component classes, and the prompt allows no others. The [report](../docs/terminology.md#8-the-pipeline) lists these component classes (below). One differing only in case, spaces or punctuation is not outside the schema: it's accepted and written in the schema's spelling. |
   | The same [subject](../docs/terminology.md#2-triples), predicate, [object](../docs/terminology.md#2-triples) and entity classes again | **removed**, reason `duplicate` | Counted once. |
   | Something that isn't a [classed triple](../docs/terminology.md#2-triples) at all | **removed**, reason `malformed` | Nothing to keep. |
   | A pattern the schema doesn't list (known component classes, new combination) | **kept**, [flag](../docs/terminology.md#2-triples) `pattern_not_in_schema` | The schema's patterns are what was seen, not all that's allowed. |
   | Any other flag (a reworded subject or [object instance](../docs/terminology.md#2-triples), subject equal to object, the same [subject instance](../docs/terminology.md#2-triples), predicate, and object instance with other entity classes) | **kept**, flagged | Often fine; worth a look. |
   | The DESCRIBES row | **always kept** | Every record extracted has one. If the model named no entity class for it, or one the schema doesn't have, its entity class is `X`, flagged `describes_undecided`. |

The flag names are listed in `050_annotate/050_annotate.md` (*Checks on each row*).

**Component classes outside the schema.** The report's table *Component classes outside the schema* lists the entity classes and predicates the model used that the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) doesn't have, most used first, each with the `source:` line an addition of it needs. Only component classes it is fair to add are counted: **held-out records are never counted** (one learned there would let held-out records influence the schema, and the held-out numbers would no longer measure records the pipeline was never adjusted to); tuning records are, and are named by [pool](../docs/terminology.md#4-ground-truth-and-samples) position (`source: ground truth tuning #0, #12`); on a [run](../docs/terminology.md#8-the-pipeline) over every record, no ground truth record is counted at all (`source: extraction over records not annotated`). The full list is in `extracted_triples_details.json`, under `new_component_classes`.

**Then the results** (`results`): the four files are written, replacing the last run's; the report.

The code: `060_extract/` holds `run.py` (the [control panel](../docs/terminology.md#8-the-pipeline): inputs, [settings](../docs/terminology.md#8-the-pipeline) and the [moves](../docs/terminology.md#8-the-pipeline), in order); `060_extract/060_extract_helpers/` holds `moves.py` (the moves, and writing the results), `records.py`, `schema.py` and `extract.py`; `060_extract/060_extract_prompts/` holds the prompts (see *Prompts*). Shared with other [steps](../docs/terminology.md#8-the-pipeline): `common/common_helpers/extraction.py` and `common/common_prompts/` (asking the model and building rows, with 050), `common/common_helpers/schema_io.py` (reading schemas), `common/common_helpers/validate.py` (the checks), `common/common_helpers/cache.py`, `common/common_helpers/llm.py`.

## Prompts

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `060_extract/060_extract_prompts/extract.txt` | [stage](../docs/terminology.md#8-the-pipeline) 3, one call per [text piece](../docs/terminology.md#1-records-and-their-text) | list only the [facts](../docs/terminology.md#2-triples) the [schema](../docs/terminology.md#3-schemas) can express, using **only** the schema's [entity classes](../docs/terminology.md#3-schemas) and [predicates](../docs/terminology.md#3-schemas) (the schema is shown in the prompt), and name the entity class of what the title names, or none if no entity class fits |
| `common/common_prompts/extraction_rules.txt` | inside `extract.txt` (`$rules`) | follow the rules shared with 050: [subject](../docs/terminology.md#2-triples) and [object](../docs/terminology.md#2-triples) in the [record](../docs/terminology.md#1-records-and-their-text)'s own words, the shortest [source text](../docs/terminology.md#1-records-and-their-text) copied exactly, one fact per [classed triple](../docs/terminology.md#2-triples), no "is a" classed triples, the kind of thing the title names |
| `common/common_prompts/extraction_reply.txt` | inside `extract.txt` (`$reply`) | reply in the JSON form shared with 050 |

Each prompt is a plain text file: open it to read exactly what the [model](../docs/terminology.md#8-the-pipeline) is told. `$name` marks where the code fills something in. The prompts speak plainly to the model ("facts", "entity classes", "predicates"), explaining any term they use. Editing a prompt is allowed: the next [run](../docs/terminology.md#8-the-pipeline) asks again every call that uses it, and pays for them. The two `common/common_prompts/` files are shared with 050: editing them changes both [steps](../docs/terminology.md#8-the-pipeline).

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the [report](../docs/terminology.md#8-the-pipeline)'s warnings):

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) of the ground truth aren't finished yet … so skipped* | Only [finished records](../docs/terminology.md#4-ground-truth-and-samples) can be evaluated. | Finish them in `py helpers/annotate.py`, or ignore. |
| *Ground truth, record … is in batch_… and batch_…: annotated twice* | A [record](../docs/terminology.md#1-records-and-their-text) is annotated twice. It's left out of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) until fixed. | Keep it in one file. |
| *Ground truth, record … (batch_…): all_facts_extracted is 0 on some rows, 1 on others* | Mixed, so the record doesn't count as finished. | Set it the same on every row (the tool's box does). |
| *Ground truth, record … (batch_…): lines … and … are the same classed triple.*, then each line | [The same classed triple twice](../docs/terminology.md#4-ground-truth-and-samples) in one record (a hand edit). Only one copy can be paired, so evaluation would count the other as missed. Step 070 refuses to run until one is deleted. | Delete one of the two rows. |
| *Ground truth, record … (batch_…): lines … and … state the same subject instance, predicate, and object instance, with different entity classes.*, then each line | Likely one fact given two [entity classes](../docs/terminology.md#3-schemas) by mistake. | If they state one fact, delete the line with the wrong entity classes. |
| *The ground truth of N of the records chosen was drafted (step 050) by …, the same model as this run's (…) / a model from the same maker (…) as this run's …* | Shown before paying. Facts that model misses tend to be missing from both the ground truth and the extraction, so recall would look better than it is (see `070_evaluate/metrics/recall.md`). The maker is read from the model's name (`common/common_helpers/llm.py`, `maker`); a model whose name the table doesn't know is compared by name only. | Rerun with `--model` naming a model from another maker (`py helpers/models.py` lists them), or go ahead for a test run. |
| *Ground truth, batch_… lacks the column(s) …; not read* | A ground truth file without one of the columns (see `annotations/README.md`). | Add the column. |
| *N record(s) you listed is/are not in the catalog / without text, so skipped* | With `ids`. | Check for typos. |
| *N ground truth record(s) is/are not in the catalog / without text, so skipped* | With `extract_from` = `ground_truth` (the default): a ground truth id that isn't in 020's records, or a record with no [text](../docs/terminology.md#1-records-and-their-text) to read. | Check the id in `annotations/ground_truth/` for typos; a record without text can't be extracted. |
| *extract_from (…) is ignored, because ids names the records.* | Both were given. | Drop one. |
| *N addition(s) … are already there (in the schema, or an earlier addition), so that entry is kept* | A clash, ignoring case and punctuation. | Remove or rename the addition. |
| *N line(s) of schema_additions.txt aren't read as an entry, a source or patterns …* | The first 5 are listed with their line numbers: usually an entity class or predicate with a space in it, one space before the definition, a [pattern](../docs/terminology.md#3-schemas) line not in the `Subject -> Object; …` form, or a repeated entry (the first is kept; the repeat and the lines under it are listed). Such a line adds nothing. | Fix the line (see *The shape of a schema*). |
| *N addition(s) … say they come from the ground truth but don't show they come from tuning records only, so they are left out* | Each is listed with why: it doesn't say `tuning`, or names a held-out record, a position not in the [pool](../docs/terminology.md#4-ground-truth-and-samples), or no record. | Take the addition out, or (if it really came from tuning records) list their [pool positions](../docs/terminology.md#4-ground-truth-and-samples): `source: ground truth tuning #12`. |
| *Entries of … whose source names ground truth records other than tuning ones (N)* | The [schema](../docs/terminology.md#3-schemas) given with `--schema` (e.g. the [hand-built schema](../docs/terminology.md#3-schemas)) has entries whose `source:` line names the ground truth but fails the check additions get: it names a held-out record, doesn't say `tuning`, names a position not in the pool, or names no record. Usually [component classes](../docs/terminology.md#3-schemas) learned from held-out records: the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) gives each one it adds there a `source:` line naming the records that use it (patterns get none, so a pattern learned from a held-out record isn't caught). They are kept. | Fine for tuning numbers. Don't trust this [run](../docs/terminology.md#8-the-pipeline)'s held-out numbers: extract with a schema that didn't learn from held-out records (040's, by default). |
| *N addition(s) have no "source:" line …* | Where the idea came from isn't recorded. | Add a `source:` line under each. |
| *N schema entries have no definition …* | The [model](../docs/terminology.md#8-the-pipeline) will see those entity classes or predicates with no definition. | Add definitions. |
| *N component class(es) used in patterns aren't in the schema* | A pattern uses something the schema doesn't have (often a typo). | Fix the pattern, or add the missing entity class or predicate. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) failed and are not in the output* | Their [model calls](../docs/terminology.md#8-the-pipeline) failed (after the model client's own retries). | Run the [step](../docs/terminology.md#8-the-pipeline) again: only those are asked again, and every answer already paid for is reused. |
| *N of M rows have no origin, so they can't be traced to the input they came from* | Should never happen: a code change dropped the field that records where each item came from. | Fix the code before using the output. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *missing input files … schema … run 040_induce_schema first, or pass --schema* | 040 hasn't run. | Run 040 (or pass `--schema`). |
| *… has no entity classes or no predicates: is it a schema?* | The `--schema` file isn't in either shape. | Check the file against *The shape of a schema* (Inputs). |
| *"entity_classes" must be a list …* / *… entry N has no "component_class"* / *patterns entry N must be …* | A JSON schema that doesn't follow the shape above. | Fix the file (see *The shape of a schema*). |
| *extract_from must be one of ground_truth, all* | A typo in the [setting](../docs/terminology.md#8-the-pipeline). | Use `ground_truth` or `all`. |
| *Nothing to extract. …* | No record could be chosen; the reasons follow. | Change the settings: the reasons are listed. |
| *… must be at least N* | A setting is out of range: `workers` under 1, or `max_chars` under 1,000. | Fix the setting. |
| *model must name a model* | The `model` setting is empty. | Give a model's name (`py helpers/models.py` lists them). |
| *Test call to … failed* | Ask Sage refuses you that model, the key is wrong, or Ask Sage can't be reached. Nothing else was called. | If Ask Sage says the model isn't allowed, choose another (`--model`; `py helpers/models.py` lists them). Otherwise check `.env` and the network. |
| *Cancelled. Nothing was spent.* | You declined at the confirmation. | — |
| *Stopped. Calls not yet started were cancelled. Answers already received are kept in the cache; nothing else was written.* | You pressed Ctrl+C while the model calls ran. | Run the step again: the answers already received are reused, not paid for again. |
| *Set ASKSAGE_EMAIL and ASKSAGE_API_KEY (e.g. in .env).* | The Ask Sage credentials aren't set, so no model can be called. | Put them in `.env` (see `docs/running_on_nasa_laptop.md`). |

## Audit trail

- **Prompts.** The [report](../docs/terminology.md#8-the-pipeline)'s *Prompts* section lists every prompt the [run](../docs/terminology.md#8-the-pipeline) filled in, each with a [fingerprint](../docs/terminology.md#8-the-pipeline) (sha256) of its exact text, so the prompt behind any answer is known even if the prompt file was edited later (`_manifest.json` keeps the full fingerprints).
- **[Log](../docs/terminology.md#8-the-pipeline).** `outputs/logs/<run id>.log` records the command line, the [settings](../docs/terminology.md#8-the-pipeline), the git commit, every [model call](../docs/terminology.md#8-the-pipeline)'s retries, each [move](../docs/terminology.md#8-the-pipeline)'s duration, each output file's hash and, on failure, the full traceback.
- **[Origin](../docs/terminology.md#8-the-pipeline).** Each kept or removed row has an `origin` column naming its [record](../docs/terminology.md#1-records-and-their-text) in 020's `records.jsonl`; `schema_used.json` names the [schema](../docs/terminology.md#3-schemas) file and additions file it was built from.
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every [step](../docs/terminology.md#8-the-pipeline)'s output to the 010 [batch file](../docs/terminology.md#1-records-and-their-text) and the API request that first returned it (`helpers/audit.md`).

## Known limits

- **Not yet run with the real [model](../docs/terminology.md#8-the-pipeline).** As of 2026-09-29, 060 has been tested only with a stand-in for the model, and with 040's [schema](../docs/terminology.md#3-schemas) from a stand-in run, because Ask Sage can't be reached from the laptop it was built on. Numbers in this guide come from the catalog, the code or the stand-in, not from a real [run](../docs/terminology.md#8-the-pipeline).
- **[Patterns](../docs/terminology.md#3-schemas) are not enforced.** A [classed triple](../docs/terminology.md#2-triples) joining two known [entity classes](../docs/terminology.md#3-schemas) with a known [predicate](../docs/terminology.md#3-schemas) is kept even if the schema never saw that combination. 070's metrics will show whether that lets in wrong [facts](../docs/terminology.md#2-triples).
- **A synonym is removed, not repaired.** A [component class](../docs/terminology.md#3-schemas) spelled differently (`Space craft`, `SPACECRAFT` for `Spacecraft`) is accepted, since component classes are compared by [loose match](../docs/terminology.md#3-schemas), and it is written in the schema's own spelling. A true synonym (`Satellite`) is removed; the [report](../docs/terminology.md#8-the-pipeline) lists it.
- **The model varies.** Rerunning with an empty cache can extract different classed triples; the cache makes a rerun reproducible.
