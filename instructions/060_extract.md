# 060_extract

Terms (triple instance, entity class, schema, pattern, DESCRIBES row, error, flag, …) are as defined in [docs/terminology.md](../docs/terminology.md).

## Purpose

Extracts, from each record's text, the facts a schema can express. A model lists them as triple instances using **only** the schema's entity classes and predicates. Code checks every one against the record's text and the schema, then keeps it or removes it with a reason. What 060 keeps is what step 070 scores against the ground truth, and what step 080 will build the graph from.

The schema is 040's induced schema by default, plus the entity classes and predicates you add by hand in `annotations/schema_additions.txt` (e.g. on a mentor's advice). By default, 060 extracts only from the records of the ground truth you've finished, the ones 070 can score. Once the schema is final, `--extract_from all` extracts from every record.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned records: the texts. |
| `schema` | `040_induce_schema/the_schema.json` | The schema to extract with. Any schema in one of the two shapes below can be given instead: `--schema <file>`. |
| `additions` | `./annotations/schema_additions.txt` (in Git) | Entity classes and predicates added by hand to whichever schema is used. Starts empty. |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | Which records have ground truth, and which are finished. |

### The shape of a schema

A schema holds entity classes and predicates, each with a one-line definition, and patterns. 060 reads two shapes, told apart by the file's ending (`common/schema_io.py`).

**JSON (`.json`), like 040's `the_schema.json`.** Only the names are required, but give each a definition: it's the model's only clue to what the name means.

```json
{"entity_classes": [{"name": "Instrument", "definition": "A device that takes measurements."},
                    {"name": "Spacecraft", "definition": "A craft that operates in space."}],
 "predicates":     [{"name": "ABOARD", "definition": "Is carried on."}],
 "patterns":       [{"pattern": ["Instrument", "ABOARD", "Spacecraft"]}]}
```

- `entity_classes` and `predicates` are lists of entries, each with `"name"` and `"definition"`.
- `patterns` is a list of `{"pattern": [subject entity class, predicate, object entity class]}`; it may be left out.
- Anything else is ignored: 040's `support`, `maintainers`, `texts`, `examples`, `deferred`, `made`. So 040's file works as it is, and so does one written by hand.

**Text (any other ending), like the hand-built schema** `annotations/schema_derived_from_manual_annotation.txt`:

```
CLASSES
-------
Instrument        a device that takes measurements
Spacecraft        a craft that operates in space

PREDICATES
----------
ABOARD            is carried on
                  Instrument -> Spacecraft; Instrument -> Aircraft
```

- An entry is its name, then **two or more spaces**, then its definition, on one line.
- Under a predicate, an indented line lists its patterns as `Subject -> Object` pairs separated by `;`.
- Under any entry, an indented line starting `source:` says where the idea came from (used by the additions file).
- Lines starting with `#`, and any other prose, are ignored.

So `py 060_extract.py --schema annotations/schema_derived_from_manual_annotation.txt` extracts with your hand-built schema.

### Adding entity classes and predicates by hand

Write them in `annotations/schema_additions.txt`, in the text shape above. It holds an example in `#` comments. For instance:

```
CLASSES
-------
Mission           a named spaceflight effort
                  source: mentor

PREDICATES
----------
PART_OF_MISSION   belongs to the mission
                  Spacecraft -> Mission
                  source: mentor
```

- They're added to whichever schema is used, marked as coming from the additions, with no support, maintainers or texts.
- An addition whose name the schema already has is left out, and the schema's entry is kept. So is one differing only in capital letters: `dataset` vs `Dataset`.
- Give each one a `source:` line saying where the **idea** came from (`mentor`, `NASA missions A-to-Z`, …). An addition without one is pointed out before paying.
- **Adding names seen in ground truth records needs care.** Step 070 scores extraction on those records, so a name added because it came up there flatters the score for exactly those records. This will be settled when 070 is built. Until then, prefer names from outside knowledge or from a run over every record (the report's list then leaves the ground truth records out).

## Outputs

In `outputs/intermediate_results/060_extract/`. Every file is rewritten by each run and holds that run's records only. Switching back to an earlier schema or set of records costs no model calls, because every answer is in `cache/`.

| File | Contents |
|---|---|
| `extracted_triples.csv` | The triple instances kept: for each record extracted, its DESCRIBES row first, then its triple instances. Columns `id, subject, subject_class, predicate, object, object_class, source_text, flags, origin`. |
| `extracted_triples_removed.csv` | Every triple instance removed, with `reason` (below; both, if both apply); `raw` holds what the model returned when it wasn't a triple instance at all. |
| `schema_used.json` | The schema this run used: the schema input plus the additions, in the JSON shape above, each entry with `"from": "schema"` or `"additions"` (and its `source`), and the additions left out for a clash (`left_out_additions`). 070 and 080 read this, so they use exactly what 060 used. |
| `extraction_details.json` | Each record chosen, with its status (`extracted`, or `failed` with the error), text pieces, rows kept and removed; the records passed over while choosing; and the names outside the schema the model used (see the report). |
| `cache/` | Every model answer, so a rerun pays only for what it doesn't have. Not listed in the manifest. |
| `_manifest.json` | Run id, settings, input files and their hashes, output hashes, headline numbers. |

For scoring: a record **missing** from `extracted_triples.csv` wasn't extracted (a failed call) and must be left out, not scored as zero. A record with **only its DESCRIBES row** was extracted and states no fact the schema can express.

Each run also leaves `outputs/reports/<run id>.md` and `outputs/logs/<run id>.log`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `extract_from` | `ground_truth` | `ground_truth`: the records of the ground truth that are finished (*All facts extracted* ticked), the only ones 070 can score. `all`: every record with text. | `all` once the schema is final. That's about one model call per record, ~36,000; the confirmation shows the number before anything is spent. |
| `ids` | empty | Extract from exactly these records instead: ids separated by commas, or the path of a text file with one id per line (as in 050). | To extract from records you choose. |
| `max_chars` | 8000 | A text longer than this is split into pieces, one model call each. | Rarely. |
| `workers` | 4 | Model calls made at the same time. | Lower it if Ask Sage refuses calls for coming too fast. |
| `confirm_paid_calls` | true | Stop and ask before the first model call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

```
py 060_extract.py                                         the finished ground truth records, with 040's schema
py 060_extract.py --schema annotations/schema_derived_from_manual_annotation.txt   with your hand-built schema
py 060_extract.py --extract_from all                      every record (once the schema is final)
py 060_extract.py --ids 3122be4c-…,cfd6ec3f-…             exactly these records
py 060_extract.py --confirm_paid_calls false              don't ask (unattended runs)
```

060 needs 040's `the_schema.json`. Until 040 has run, it stops with *missing input files … run 040_induce_schema first, or pass --schema*.

**Paying.** Before its first model call, 060 logs its plan (how many records, how many calls, the model) and waits: Enter starts, anything else stops the run having spent nothing. Anything that makes the run differ from what you asked (listed under *Checks and warnings*) is shown first, above the question, so you can cancel and fix it. The first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: one per record, plus one per extra piece of a long text, plus the test call.

## How it works

Four stages, in `060_extract.py`'s `main()`:

1. **Pick the records** (`records.py`). By `extract_from` or `ids` (above). Anything that differs from what was asked becomes a note shown before paying: a listed id not in the catalog or without text, ground truth records not yet finished.
2. **Load the schema** (`schema.py`). The schema input plus the additions, merged, each entry remembering where it came from. Notes: additions that clash with the schema, additions with no `source:` line, entries with no definition, pattern names that aren't entity classes or predicates of the schema.
3. **Ask the model** (`extract.py`). One call per text piece, with the prompt `prompts/extract.txt`: extract only the facts the schema can express, in only the schema's names, and name the entity class of what the title names (`describes_class`), or none if no class fits. The model sees the schema in the text shape above. The rules and the reply format are 050's (`common/prompts/`), so what 060 extracts and the ground truth 050 drafted are asked for the same way. The calls are made by `common/extraction.py`, as in 050: every answer is cached the moment it arrives, and a record with a failed call is left out whole, never half extracted.
4. **Check and sort the rows** (`extract.py`, code). `common/extraction.py` builds each record's rows (the DESCRIBES row first) and checks every one against the record's **whole** text and the schema (`common/validate.py`). Then:

| What | Where it goes | Why |
|---|---|---|
| Its source text is missing, or isn't in the record's text | **removed**, reason `source_text` | It can't be verified, and may be invented. |
| An entity class or predicate the schema doesn't have | **removed**, reason `name_not_in_schema` | The graph can only hold the schema's names, and the prompt allows no others. The report lists these names (below). A name differing only in case, spaces or punctuation is not outside the schema: it's accepted and written in the schema's spelling. |
| The same subject, predicate, object and entity classes again | **removed**, reason `duplicate` | Counted once. |
| Something that isn't a triple instance at all | **removed**, reason `malformed` | Nothing to keep. |
| A pattern the schema doesn't list (known names, new combination) | **kept**, flag `pattern_not_in_schema` | The schema's patterns are what was seen, not all that's allowed. |
| Any other flag (a reworded name, subject equal to object, the same triple instance with other entity classes) | **kept**, flagged | Often fine; worth a look. |
| The DESCRIBES row | **always kept** | Every record extracted has one. If the model named no entity class for it, or one the schema doesn't have, its class is `X`, flagged `describes_undecided`. |

The flag names are listed in `instructions/050_annotate.md` (*Checks on each row*).

**Names outside the schema.** The report lists the entity classes and predicates the model used that the schema doesn't have, most used first. A name that keeps coming back may belong in `schema_additions.txt`. On a run over every record, the ground truth records are left out of that count, so names learned there don't come from the records 070 scores.

The code: `060_extract/` holds `moves.py` (the moves, and writing the results), `records.py`, `schema.py`, `extract.py` and `prompts/`. Shared with other steps: `common/extraction.py`, `common/prompts/`, `common/schema_io.py`, `common/validate.py`, `common/cache.py`.

## Checks and warnings

Shown **before paying** (and in the report's warnings):

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) of the ground truth aren't finished yet … so skipped* | Only finished records can be scored. | Finish them in `py annotate.py`, or ignore. |
| *N record(s) you listed is/are not in the catalog / without text, so skipped* | With `ids`. | Check for typos. |
| *extract_from (…) is ignored, because ids names the records.* | Both were given. | Drop one. |
| *N addition(s) … have a name the schema already has, so the schema's entry is kept* | A clash, ignoring capital letters. | Remove or rename the addition. |
| *N addition(s) have no "source:" line …* | Where the idea came from isn't recorded. | Add a `source:` line under each. |
| *N schema entries have no definition …* | The model will see only the name. | Add definitions. |
| *N name(s) used in patterns aren't entity classes or predicates of the schema* | A pattern names something the schema doesn't have (often a typo). | Fix the pattern, or add the name. |

In the report only:

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) failed and are not in the output* | Their model calls failed (after the model client's own retries). | Run again: only they are asked again. |

The step stops, having spent nothing, with:

| Message | Meaning |
|---|---|
| *missing input files … schema … run 040_induce_schema first, or pass --schema* | 040 hasn't run. |
| *… has no entity classes or no predicates: is it a schema?* | The `--schema` file isn't in either shape. |
| *"entity_classes" must be a list …* / *… entry N has no "name"* / *patterns entry N must be …* | A JSON schema that doesn't follow the shape above. |
| *extract_from must be one of ground_truth, all* | A typo in the setting. |
| *Nothing to extract. …* | No record could be chosen; the reasons follow. |
| *… must be at least …* | A setting out of range. |
| *Test call to … failed* | The model name or the key is wrong, or Ask Sage can't be reached. |
| *Cancelled. Nothing was spent.* | You declined at the confirmation. |

## Human work

- **Read the removed file and the list of names outside the schema** now and then. A rule that removes good facts, or a name the model keeps reaching for, is a sign the schema (or the prompt) needs work.
- **Keep `schema_additions.txt` sourced.** Every addition gets a `source:` line.

## Known limits

- **Not yet run with the real model.** As of 2026-09-29, 060 has been tested only with a stand-in for the model, and with 040's schema from a stand-in run, because Ask Sage can't be reached from the laptop it was built on.
- **Patterns are not enforced.** A triple instance joining two known entity classes with a known predicate is kept even if the schema never saw that combination. 070's scores will show whether that lets in wrong facts.
- **A synonym is removed, not repaired.** A name spelled differently (`Space craft`, `SPACECRAFT` for `Spacecraft`) is accepted, since names are compared on letters and digits only, ignoring case, and it is written in the schema's own spelling. A true synonym (`Satellite`) is removed; the report lists it.
- **The model varies.** Rerunning with an empty cache can extract different triple instances; the cache makes a rerun reproducible.
