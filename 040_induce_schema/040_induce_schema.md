# 040_induce_schema

Terms ([triple instance](../docs/terminology.md#2-triples), [component instance](../docs/terminology.md#2-triples), [label](../docs/terminology.md#5-learning-the-schema-step-040), [support](../docs/terminology.md#5-learning-the-schema-step-040), …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Learning the schema (step 040)*.

## Purpose

Learns the [schema](../docs/terminology.md#3-schemas) from the catalog itself, instead of writing it in advance:

- **[entity classes](../docs/terminology.md#3-schemas)**: the types of things the [texts](../docs/terminology.md#1-records-and-their-text) talk about, e.g. `Instrument`, `Spacecraft`;
- **[predicates](../docs/terminology.md#3-schemas)**: the relations between them, e.g. `ABOARD`;
- **[patterns](../docs/terminology.md#3-schemas)**: which entity classes each predicate joins, e.g. `Instrument ABOARD Spacecraft`.

A [model](../docs/terminology.md#8-the-pipeline) reads a sample of texts and lists the [triple instances](../docs/terminology.md#2-triples) they state, with no schema imposed; code keeps only those it can verify in the text. The model gives every [component instance](../docs/terminology.md#2-triples) a [label](../docs/terminology.md#5-learning-the-schema-step-040) and merges labels that mean the same thing. Code counts the [support](../docs/terminology.md#5-learning-the-schema-step-040) of each [schema entry](../docs/terminology.md#3-schemas) (how many texts, and how many [maintainers](../docs/terminology.md#1-records-and-their-text), back it), and keeps every schema entry with that [evidence](../docs/terminology.md#5-learning-the-schema-step-040). The schema is judged downstream: 070 measures how much of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) it can express (its [recall upper bound](../docs/terminology.md#7-evaluating-extraction-step-070)) and how well extraction does with it.

## To do

What to do, and when, is in [`docs/upkeep.md`](../docs/upkeep.md), one page for every step; `py run_pipeline.py --status` (or the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples)'s home page) lists what is waiting now. For this step, in short:

- Choose the model before the real run ([*Before the first run*](../docs/upkeep.md#before-the-first-run)).
- After running, review the merges and read *Saturation* in the report ([*Running the steps again*](../docs/upkeep.md#running-the-steps-again)).
## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned [records](../docs/terminology.md#1-records-and-their-text): the [texts](../docs/terminology.md#1-records-and-their-text). |
| `splits` | `030_split/splits.json` | 030's [induction candidates](../docs/terminology.md#4-ground-truth-and-samples): every [maintainer](../docs/terminology.md#1-records-and-their-text)'s records that may be learned from, each maintainer's in a fixed random order. |
| `ground_truth_schema` | `./annotations/ground_truth_schema.txt` (in Git) | The [ground truth schema](../docs/terminology.md#3-schemas), written while annotating [ground truth](../docs/terminology.md#4-ground-truth-and-samples). Only compared with, in the [report](../docs/terminology.md#8-the-pipeline); it doesn't shape the [induced schema](../docs/terminology.md#5-learning-the-schema-step-040). |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | The ground truth: its patterns count as the ground truth schema's when comparing (none yet is fine). |

## Outputs

In `outputs/intermediate_results/040_induce_schema/`:

**On a rerun:** both files are replaced; `cache/` keeps every answer, so only calls not asked before are paid.

| File | Contents |
|---|---|
| `the_schema.json` | The [schema](../docs/terminology.md#3-schemas): [entity classes](../docs/terminology.md#3-schemas), [predicates](../docs/terminology.md#3-schemas), and [patterns](../docs/terminology.md#3-schemas), each with its [evidence](../docs/terminology.md#5-learning-the-schema-step-040); and every [schema entry](../docs/terminology.md#3-schemas) [deferred](../docs/terminology.md#5-learning-the-schema-step-040), with why. |
| `induction_evidence.json` | Everything the schema was built from: each [text](../docs/terminology.md#1-records-and-their-text)'s `describes_class`, its [verified triple instances](../docs/terminology.md#2-triples) and the ones left out as [unverified](../docs/terminology.md#2-triples) (with why), the texts left out because a model call failed (`failed_texts`), every [component instance](../docs/terminology.md#2-triples)'s [label](../docs/terminology.md#5-learning-the-schema-step-040) (`labels`), the labels each kind ended with (`vocabulary`), the component instances left unlabeled (`unlabeled`), what the model refused to label or define (`refused`), the labeling batches, every merge and [spelling fold](../docs/terminology.md#3-schemas), all counts (including schema entries not in the schema), the merges the model got wrong (`merge_issues`), the entries too vague to define (`too_vague`), the definitions, the [model calls](../docs/terminology.md#8-the-pipeline) made, and the comparison with the [ground truth schema](../docs/terminology.md#3-schemas). |
| `cache/` | Every [model](../docs/terminology.md#8-the-pipeline) answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the [manifest](../docs/terminology.md#8-the-pipeline). |
| `_manifest.json` | [Run id](../docs/terminology.md#8-the-pipeline), [settings](../docs/terminology.md#8-the-pipeline), input files and their hashes, output files and their hashes, headline numbers, and the [harvest](../docs/terminology.md#1-records-and-their-text) date. Written when a [run](../docs/terminology.md#8-the-pipeline) finishes. |

`the_schema.json`, shortened:

```json
{"entity_classes": [{"component_class": "Instrument", "definition": "A device that takes measurements.",
                     "examples": ["MODIS", "AIRS", "CERES"], "support": 34,
                     "maintainers": ["Earthdata Forum", "…"], "texts": ["…"],
                     "_origin": ["020_clean/records.jsonl#…", "…"]}, …],
 "predicates": [{"component_class": "ABOARD", "definition": "…", "examples": ["MODIS -- is aboard -- Aqua", "…"], "support": 21, "maintainers": ["…"],
                 "texts": ["…"], "_origin": ["…"]}, …],
 "patterns": [{"pattern": ["Instrument", "ABOARD", "Spacecraft"], "support": 19,
               "maintainers": ["…"], "texts": ["…"], "_origin": ["…"]}, …],
 "deferred": [{"entry_type": "entity class", "schema_entry": "Thing", "support": 40, "reason": "too vague: …"}, …],
 "made": {"run_id": "040_induce_schema_…", "model": "…", "settings": {…}, "texts": 150,
          "maintainers": ["…"]}}
```

| Field | Meaning |
|---|---|
| `support` | The schema entry's [support](../docs/terminology.md#5-learning-the-schema-step-040): how many different texts it was found in. |
| `maintainers` | The [maintainers](../docs/terminology.md#1-records-and-their-text) those texts came from. Support from many is a catalog-wide regularity; support from one may be that maintainer's house style. |
| `texts`, `_origin` | The [records](../docs/terminology.md#1-records-and-their-text) whose texts it was found in (see `helpers/audit.md`). |
| `examples` | Picked by code: for an entity class, the component instances that most often got it; for a predicate, the [triple instances](../docs/terminology.md#2-triples) that most often state it ("subject -- predicate -- object"), which show its subject and object. |
| `deferred` | Every schema entry found but not in the schema: support below `min_support`, judged too vague by the model, or a pattern through a schema entry that isn't in the schema. |

Each run also leaves `outputs/reports/<run id>.md` (the [report](../docs/terminology.md#8-the-pipeline): what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `induction_maintainers` | 10 | Learn from this many of the largest [maintainers](../docs/terminology.md#1-records-and-their-text). | To cover more (or fewer) of the catalog's maintainers. |
| `texts_per_maintainer` | 15 | Take the first this-many [induction candidates](../docs/terminology.md#4-ground-truth-and-samples) of each. | To learn from more [text](../docs/terminology.md#1-records-and-their-text). Taking more keeps the texts already taken, so their extraction calls are reused (see How to run). |
| `min_support` | 1 | A [schema entry](../docs/terminology.md#3-schemas) enters the [schema](../docs/terminology.md#3-schemas) if its [support](../docs/terminology.md#5-learning-the-schema-step-040) is at least this. 1 keeps everything found. | Once 070's metrics can compare values; see Known limits. |
| `max_chars` | 8000 | A text longer than this is split into [text pieces](../docs/terminology.md#1-records-and-their-text), one [model call](../docs/terminology.md#8-the-pipeline) each (`common/common_helpers/chunking.py`). | Rarely. No text of the default sample is that long (the longest is 5,797 characters). |
| `workers` | 4 | Model calls made at the same time. | Lower it if the service refuses calls for coming too fast. |
| `service` | litellm | The service that reaches the model: `asksage` (NASA's Ask Sage) or `litellm` (NASA's LiteLLM). Each has its own key in `.env` and its own model names. Every cached answer is tied to its service and model. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `model` | claude-opus-5.5 | The AI [model](../docs/terminology.md#8-the-pipeline) to ask. `py helpers/models.py --service <service>` lists the models the service shows your account; a listed one may still refuse you, which the [run](../docs/terminology.md#8-the-pipeline)'s [test call](../docs/terminology.md#8-the-pipeline) finds out for the price of that call. Every cached answer is tied to its model (and service): another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `confirm_paid_calls` | true | Stop and ask before the first model call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), on a computer that can reach the model's service and has its key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 040_induce_schema/run.py --help                           every input and setting, with its default
py 040_induce_schema/run.py                                  learn from 150 texts; asks before paying
py 040_induce_schema/run.py --texts_per_maintainer 30        learn from more text
py 040_induce_schema/run.py --confirm_paid_calls false       don't ask (unattended runs)
```

**Paying.** Before its first [model call](../docs/terminology.md#8-the-pipeline), 040 logs its plan (how many extraction calls, the [model](../docs/terminology.md#8-the-pipeline)) and waits: Enter starts, anything else stops the [run](../docs/terminology.md#8-the-pipeline) having spent nothing. If the run can't do exactly what you asked, it says so first, above the question (*Step 040 found N warnings:*, then each one, numbered; they're listed under *Checks and warnings*). Its first call is the [test call](../docs/terminology.md#8-the-pipeline), which checks that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: about one per [text](../docs/terminology.md#1-records-and-their-text) to extract [triple instances](../docs/terminology.md#2-triples), plus a few dozen to [label](../docs/terminology.md#5-learning-the-schema-step-040), merge, and define; the [report](../docs/terminology.md#8-the-pipeline) counts each [stage](../docs/terminology.md#8-the-pipeline)'s calls exactly.

**The cache.** Every model answer is kept in `cache/`, under a [fingerprint](../docs/terminology.md#8-the-pipeline) of everything that decided it: the model and its service, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed; editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again. Taking more texts (`texts_per_maintainer`, `induction_maintainers`) reuses every text's extraction already made and pays only for the new texts.

## How it works

Seven [stages](../docs/terminology.md#8-the-pipeline), in `040_induce_schema/run.py`'s `main()`; stages 2, 3, 4, and 6 ask the [model](../docs/terminology.md#8-the-pipeline), the others are code:

1. **Pick the [texts](../docs/terminology.md#1-records-and-their-text)** (`texts.py`, `pick_texts`). From 030's [induction candidates](../docs/terminology.md#4-ground-truth-and-samples), the first `texts_per_maintainer` [records](../docs/terminology.md#1-records-and-their-text) of each of the `induction_maintainers` largest [maintainers](../docs/terminology.md#1-records-and-their-text): 150 texts by default. Each text is the record's title and notes (and any extra text [fields](../docs/terminology.md#1-records-and-their-text) 020 kept), split into [text pieces](../docs/terminology.md#1-records-and-their-text) only if it's longer than `max_chars`, with the title repeated at the top of each piece (when the title is shorter than a quarter of `max_chars`).
2. **Extract [triple instances](../docs/terminology.md#2-triples), and check them** (`extract.py`, `extract_triple_instances`). One [model call](../docs/terminology.md#8-the-pipeline) per text piece: list every [fact](../docs/terminology.md#2-triples) the text states as a triple instance, with the text's own words as its [subject instance](../docs/terminology.md#2-triples) and [object instance](../docs/terminology.md#2-triples) and a short verb phrase in the model's words as its [predicate instance](../docs/terminology.md#2-triples) ("MODIS" – "is aboard" – "Aqua"), each with its [source text](../docs/terminology.md#1-records-and-their-text), the shortest passage that states it, copied exactly. Nothing tells the model what types of things or relations to look for. Everything else is shared with steps 050 and 060 (`common/common_helpers/extraction.py`), so the [schema](../docs/terminology.md#3-schemas) is learned from the same type of facts extraction later has to produce: the extraction rules, the reply format (without [entity classes](../docs/terminology.md#3-schemas), which stage 3 learns), and the model calls themselves (a text with a failed call is left out whole, and asked again on the next run). The reply also names `describes_class`: the type of thing the text's title names ("Dataset", "WebTool", …), judged from the whole text; the first piece to name one decides it. [Steps](../docs/terminology.md#8-the-pipeline) 050 and 060 need such entity classes for every record's [describes triple](../docs/terminology.md#2-triples), so this makes sure the schema has them. Then code checks every triple instance against its record's whole text (`common/common_helpers/validate.py`, shared with 050 and 060):
   - **[unverified](../docs/terminology.md#2-triples), left out** (may be invented): a triple instance with no source text, or whose source text isn't in the text. It counts toward nothing in the later stages, and is listed with why in `induction_evidence.json`;
   - **verified, flagged**: a triple instance whose [subject](../docs/terminology.md#2-triples) instance or [object](../docs/terminology.md#2-triples) instance isn't in the text or in its own source text (usually reworded, "the instrument" for "MODIS"), or whose subject instance and object instance are the same. The [flags](../docs/terminology.md#2-triples) are counted in the [report](../docs/terminology.md#8-the-pipeline).

   "In the text" means found once [evened out](../docs/terminology.md#2-triples). A triple instance two pieces of one text both state counts once; an item that isn't a triple instance is dropped and counted.
3. **[Label](../docs/terminology.md#5-learning-the-schema-step-040) every [component instance](../docs/terminology.md#2-triples), with a [running vocabulary](../docs/terminology.md#5-learning-the-schema-step-040)** (`label.py`, `label_component_instances`). A subject or object instance gets an entity class label ("MODIS" → `Instrument`); a predicate instance gets a [predicate](../docs/terminology.md#3-schemas) label ("is aboard" → `ABOARD`). Each is judged by the shortest triple instance it appears in. A text's title isn't sent: its label is its `describes_class` from stage 2, and those labels start the running vocabulary of entity class labels (most common first), so subject and object instances reuse them. The component instances go to the model in batches of 80, most common first, and every batch is shown the labels chosen so far, with the instruction to reuse one whenever it fits and coin a new one only when none does. So one idea doesn't end up under several labels because its component instances were in different batches. One left unlabeled is asked once more; if still unlabeled, it's listed and counts toward no [schema entry](../docs/terminology.md#3-schemas).
4. **Merge synonymous labels** (`merge.py`, `merge_labels`). A few synonyms can still slip through stage 3, so the finished list of labels goes to the model in one call per kind (entity class labels, predicate labels), each label with the number of texts it was found in and the component instances that most often got it (a text's title counts under its `describes_class`, as in stage 5, so a label used only for titles has its texts and titles too). Every label is seen beside every other. The model lists only the merges it finds (`Sensor` → `Instrument`); predicates pointing in opposite directions are never merged. Code checks the reply: a merge must go into a label that was sent; labels that weren't sent are ignored; a label merged twice keeps the first merge; chains are followed to their end. Every merge is listed in the report (`outputs/reports/040_induce_schema_<date>_<time>.md`), section *Results*, subsection *Triple instances and labels*.
5. **Count the [evidence](../docs/terminology.md#5-learning-the-schema-step-040)** (`count.py`, `count_support`). Each [verified triple instance](../docs/terminology.md#2-triples) becomes, through the labels of its component instances, a [subject class](../docs/terminology.md#2-triples), an [object class](../docs/terminology.md#2-triples), a predicate, and, if all three are labeled, a [pattern](../docs/terminology.md#3-schemas). Each text's title also counts once toward its label, as an entity class, whether or not it is in a triple instance. For every schema entry: its [support](../docs/terminology.md#5-learning-the-schema-step-040), which texts, and which maintainers. Labels that differ only in case, spacing, or punctuation are folded into one first (digits are kept: `Level2` and `Level3` stay apart); every fold is listed in `induction_evidence.json` (the report shows the first 20).
6. **Write definitions** (`define.py`, `write_definitions`). Every entity class and predicate whose support reaches `min_support` goes to the model, 40 at a time, with its support and up to 5 examples (stage 5's; `the_schema.json` keeps the first 3), for one defining sentence each, or a reason if it's too vague to tell anything apart ("Thing"). This stage only writes words; it merges and chooses nothing.
7. **Build the schema** (`check.py`, `check_schema`). The schema is built from stage 5's counts, never from the model's replies: an entity class or predicate is in it if its support reaches `min_support` and it isn't too vague; a pattern is in it if its support reaches `min_support` and its two entity classes and its predicate are in it. Every other schema entry is [deferred](../docs/terminology.md#5-learning-the-schema-step-040), with its reason. A schema entry missing its definition stays in, marked, and is listed.

Then, for the report only, **the [induced schema](../docs/terminology.md#5-learning-the-schema-step-040) is put beside the [ground truth schema](../docs/terminology.md#3-schemas)** (`compare.py`, code, comparing [component classes](../docs/terminology.md#3-schemas) with `common/common_helpers/triples_io.component_class_key`): which entity classes, predicates, and patterns both have, which only the ground truth schema has, and which only the induced one has. Component classes match when they are a [loose match](../docs/terminology.md#3-schemas), so a concept the two name differently (`Instrument`, `Sensor`) counts as unmatched. It's a sanity check on what the data taught the model, not a metric: 070 measures how much of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) the schema can express.

**Then the results** (`results`): `the_schema.json` and `induction_evidence.json` are written, replacing the last run's (whose versions are kept in `previous_runs/<run id>/` when they differ: `helpers/audit.md`, *Where to look*); the report. Its subsection *Twins in the pool* (section *Results*) counts the pool records with the same title, the same `notes`, or both as one of the texts this run learned from, by [twin kind](../docs/terminology.md#7-evaluating-extraction-step-070), beside the same counts against every induction candidate (`070_evaluate/070_evaluate.md`, *Twins*). The headline (top of the report, and the pipeline report's table *Pipeline at a glance*) gives the number of twins in the pool.

The code: `040_induce_schema/` holds `run.py` (the [control panel](../docs/terminology.md#8-the-pipeline): inputs, [settings](../docs/terminology.md#8-the-pipeline), and the [moves](../docs/terminology.md#8-the-pipeline), in order); `040_induce_schema/040_induce_schema_helpers/` holds `moves.py` (the moves, and writing the results), one file per stage (above) and `compare.py`; `040_induce_schema/040_induce_schema_prompts/` holds the prompts (see *Prompts*). Shared with other steps: `common/common_helpers/validate.py` and `common/common_helpers/text_match.py` (the checks), `common/common_helpers/schema_io.py` (reading the ground truth schema), `common/common_helpers/chunking.py` (text pieces), `common/common_helpers/cache.py` (the answer cache), `common/common_helpers/llm.py` (the model).

**Why "undefined" is one of the maintainers learned from:** it is the 5th largest (989 records whose maintainer the catalog itself gives as `undefined`); see `030_split/030_split.md`, *Why "undefined" counts as a maintainer*.

### Saturation

Would more texts have added schema entries? After counting (stage 5), and with no [model call](../docs/terminology.md#8-the-pipeline), the report's subsection *Saturation* (section *Results*) answers with a curve and a table (code: `040_induce_schema/040_induce_schema_helpers/saturation.py`; the numbers are also in `induction_evidence.json`, key `saturation`).

**The curve.** For k = 25, 50, … texts, how many [entity classes](../docs/terminology.md#3-schemas), predicates, and patterns would have reached `min_support` had 040 read only k of its texts. *Suppose* 040 read 4 texts with `min_support` 2, and an entity class was found in T1, T2, and T3. *Then* read in the order T1, T2, T3, T4 it enters the schema after 2 texts; read T4, T1, T3, T2, after 3. No order is the right one, so the curve averages over every order the texts could have been read in. It does so exactly, by a formula (the hypergeometric probability that k texts drawn from the N include at least `min_support` of the entry's texts, summed over the entries), with no random draw. The column *Added by the last 25 texts* is the one to read: near 0, more texts of the same type would barely change the schema; well above 0, the schema was still growing.

**The breadth table.** For each [schema entry](../docs/terminology.md#3-schemas), how many maintainers' texts it was found in: 1, 2, or 3 or more. An entry found in one maintainer's texts only is that maintainer's own vocabulary; many such suggest the maintainers 040 doesn't read have their own too.

**Source.** It is ecology's sample-based species accumulation curve, which judges whether a survey has found most species: a text plays the part of a sample, a schema entry that of a species (Gotelli & Colwell 2011, "Estimating species richness", in Magurran & McGill (eds), *Biological Diversity: Frontiers in Measurement and Assessment*, ch. 4: the curve is "the statistical expectation of the (sample-based) species accumulation curve" over the orders of the samples). The same idea, "saturation", decides how many interviews are enough in qualitative research (Guest, Bunce & Johnson 2006, *Field Methods* 18(1): new codes tracked after each set of six interviews; 92% of all codes had appeared by twelve). In [knowledge graph](../docs/terminology.md#8-the-pipeline) work, GrOIL (arXiv:2608.22135) tracks how its ontology grows as documents are added, in one order. Averaging over every order, with a minimum support, to judge a schema-induction sample is this project's application of the ecology method; no knowledge graph paper found does that.

**Limits.** It is descriptive: it gives no verdict and no test, and where to call the curve flat is a judgment. It speaks only for what the sample was drawn from (by default 15 texts from each of the 10 largest maintainers), not for the maintainers 040 doesn't read; the breadth table is only a hint about those. It is slightly optimistic: it uses the labels 040 chose with every text in view, and a smaller sample might have labeled a few [component instances](../docs/terminology.md#2-triples) differently. It counts entries by support alone, before the check that leaves out entries the model judged too vague. Whether a bigger or wider sample makes extraction better is a question for the evaluation (`helpers/compare_runs.md`), not for this curve.

## Prompts

In `040_induce_schema/040_induce_schema_prompts/`:

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `extract.txt` | stage 2, one call per [text piece](../docs/terminology.md#1-records-and-their-text) | list every fact the text states as subject, predicate, object, the predicate a short verb phrase in the model's own words (no schema is given), each with its [source text](../docs/terminology.md#1-records-and-their-text); and name the type of thing the title names (`describes_class`) |
| `common/common_prompts/extraction_rules.txt` | inside `extract.txt` (`$rules`) | follow the rules shared with 050 and 060 (see `050_annotate/050_annotate.md`, *Prompts*) |
| `common/common_prompts/extraction_reply.txt` | inside `extract.txt` (`$reply`) | reply in the JSON form shared with 050 and 060, without [entity classes](../docs/terminology.md#3-schemas) |
| `label_entity_instances.txt` | stage 3, 80 per call | give each [subject instance](../docs/terminology.md#2-triples) or [object instance](../docs/terminology.md#2-triples) a general [label](../docs/terminology.md#5-learning-the-schema-step-040) ("MODIS" → `Instrument`), reusing the labels chosen so far |
| `label_predicate_instances.txt` | stage 3, 80 per call | give each [predicate instance](../docs/terminology.md#2-triples) a general label ("is aboard" → `ABOARD`), reusing the labels chosen so far |
| `merge_entity_classes.txt` | stage 4, one call | list the entity class labels that mean the same thing |
| `merge_predicates.txt` | stage 4, one call | list the predicate labels that mean the same thing (never ones pointing in opposite directions) |
| `define_entity_classes.txt` | stage 6, 40 per call | write one defining sentence per entity class, or say it's too vague |
| `define_predicates.txt` | stage 6, 40 per call | write one defining sentence per predicate, or say it's too vague |

Each prompt is a plain text file: open it to read exactly what the [model](../docs/terminology.md#8-the-pipeline) is told. `$name` marks where the code fills something in. The prompts speak plainly to the model ("facts", "subjects and objects", "entity classes"), explaining any term they use. Editing a prompt is allowed: the next [run](../docs/terminology.md#8-the-pipeline) asks again every call that uses it, and pays for them.

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the [report](../docs/terminology.md#8-the-pipeline)'s warnings):

| Message | Meaning | What to do |
|---|---|---|
| *You asked for N texts from each maintainer (texts_per_maintainer), but M maintainer(s) don't have that many* | Those [maintainers](../docs/terminology.md#1-records-and-their-text) have fewer [records](../docs/terminology.md#1-records-and-their-text) to learn from ([induction candidates](../docs/terminology.md#4-ground-truth-and-samples)) than asked for, so fewer [texts](../docs/terminology.md#1-records-and-their-text) are used (each one's count is in the report (`outputs/reports/040_induce_schema_<date>_<time>.md`), section *Results*, subsection *What this run worked on*). | Nothing, or lower `texts_per_maintainer`. |
| *You asked for N maintainers (induction_maintainers), but only M have records to learn from* | Asked for more maintainers than there are; all of them are used. | Lower `induction_maintainers`. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N record(s) failed: a model call for one of their text pieces failed, so each is left out of the evidence whole* | A [model call](../docs/terminology.md#8-the-pipeline) for a [text piece](../docs/terminology.md#1-records-and-their-text) of those records failed (after the model client's own retries), so each is left out whole, never half counted. The report gives each record's id and why. | Run the step again: only the failed pieces are asked again, and every answer already paid for is reused. If the warning says some answers were cut off at the length limit, a rerun would only repeat that: first lower `max_chars`, or raise `MAX_ANSWER_TOKENS` in `common/common_helpers/llm.py`. |
| *The service refused to answer about N item(s), even asked alone* | The model's service withheld its answer (e.g. its content filter) for these [component instances](../docs/terminology.md#2-triples) (stage 3) or schema entries (stage 6). Each batch it refused was asked again in halves, down to single items (`ask_split` in `common/common_helpers/cache.py`), so only these are missing: a refused component instance stays unlabeled, a refused [schema entry](../docs/terminology.md#3-schemas) gets no definition. | Nothing if few. Each is in `induction_evidence.json` under `refused`, and what the model wrote before the stop is in the run's log (DEBUG lines starting "answer stopped by the service"). If many, try another model (`--model`). |
| *N texts gave no verified triple instance* | The model found none, or none it listed could be verified in the text. | Look at the texts and their `unverified` list in the [evidence](../docs/terminology.md#5-learning-the-schema-step-040) file; usually very short records. |
| *N component instances were left unlabeled even after a second try* | The model skipped them twice. They count toward no schema entry. | Nothing, if few. Listed in `induction_evidence.json` under `unlabeled`. |
| *The merge reply had items code ignored* | The model proposed a merge into something that isn't a [label](../docs/terminology.md#5-learning-the-schema-step-040), named labels it wasn't sent, merged a label twice, or merged a label into one already merged into it (a cycle: A into B, then B into A). Each time the first merge is kept. | Nothing: they were ignored. Listed in `induction_evidence.json` under `merge_issues`. |
| *N schema entries have no definition* | The model didn't define them. They stay in the [schema](../docs/terminology.md#3-schemas), marked. | To ask again, delete `outputs/intermediate_results/040_induce_schema/cache/define.json`, then run `py 040_induce_schema/run.py` again. |
| *The definition replies named N schema entries that weren't sent* | Ignored. | Nothing. Listed under `unknown_schema_entries`. |
| *N of M entity classes (or predicates, or patterns) have no origin, so they can't be traced to the input they came from* | Should never happen: a code change dropped the field that records where each item came from. | Fix the code before using the output. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *… labels are more than one call takes* | Over 800 labels of one [kind](../docs/terminology.md#3-schemas): too many to merge in one call. | Learn from fewer texts (lower `--texts_per_maintainer` or `--induction_maintainers`), then run `py 040_induce_schema/run.py` again (see *Known limits*). |
| *missing input files, so the step can't run:*, then one line per missing file, e.g. *records: … (run `py 020_clean/run.py` first, or give another file with --records)*, or *ground_truth_schema: … (give the file with --ground_truth_schema)* | An input file isn't there: usually an earlier step hasn't run. | Run the steps in order, or pass the file with `--<input>`. |
| *… must be at least N* | A [setting](../docs/terminology.md#8-the-pipeline) is out of range: `induction_maintainers`, `texts_per_maintainer`, `min_support` or `workers` under 1, or `max_chars` under 1,000. | Fix the setting. |
| *Induction candidate … is not in 020's records (…): … and the records are out of step* | 020 was rerun on a different [harvest](../docs/terminology.md#1-records-and-their-text) after 030 wrote `splits.json`. | Delete 030's `splits.json`, then run `py 030_split/run.py` (it writes the file only once), then run `py 040_induce_schema/run.py` again. |
| *The setting model is empty …*, *The setting service is …*, *Test call to … failed*, *… isn't set, so no model can be called*, *Cancelled. Nothing was spent.*, *Stopped with Ctrl+C. …* | The stops every step that calls the model shares. | `docs/running_on_nasa_laptop.md`, section 7, says what each means and what to do. |

## Audit trail

- **Prompts.** The [report](../docs/terminology.md#8-the-pipeline)'s *Prompts* section lists every prompt the [run](../docs/terminology.md#8-the-pipeline) filled in, each with a [fingerprint](../docs/terminology.md#8-the-pipeline) (sha256) of its exact text, so the prompt behind any answer is known even if the prompt file was edited later (`_manifest.json` keeps the full fingerprints).
- **[Log](../docs/terminology.md#8-the-pipeline).** `outputs/logs/<run id>.log` records the command line, the [settings](../docs/terminology.md#8-the-pipeline), the git commit, every [model call](../docs/terminology.md#8-the-pipeline)'s retries, each [move](../docs/terminology.md#8-the-pipeline)'s duration, each output file's hash and, on failure, the full traceback.
- **[Origin](../docs/terminology.md#8-the-pipeline).** Each [schema entry](../docs/terminology.md#3-schemas)'s `_origin` names the 020 [records](../docs/terminology.md#1-records-and-their-text) whose [texts](../docs/terminology.md#1-records-and-their-text) it was found in, e.g. `020_clean/records.jsonl#a1b2…`; `induction_evidence.json` keeps every text's [triple instances](../docs/terminology.md#2-triples) and [labels](../docs/terminology.md#5-learning-the-schema-step-040).
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every [step](../docs/terminology.md#8-the-pipeline)'s output to the 010 [batch file](../docs/terminology.md#1-records-and-their-text) and the API request that first returned it (`helpers/audit.md`). An [entity class](../docs/terminology.md#3-schemas) or a [predicate](../docs/terminology.md#3-schemas) of the [schema](../docs/terminology.md#3-schemas) can be traced too: `py helpers/audit.py Instrument`.

## Known limits

- **Run with the real [model](../docs/terminology.md#8-the-pipeline) since 2026-10-12** (`claude-opus-5.5` through LiteLLM). What those runs measured, including how much the schema varies from [run](../docs/terminology.md#8-the-pipeline) to run, is in `docs/findings.md`.
- **Adding [texts](../docs/terminology.md#1-records-and-their-text) relabels.** Taking more texts reuses every extraction already made, but labeling ([stage](../docs/terminology.md#8-the-pipeline) 3), merging (4), and definitions (6) are asked again when the set of [component instances](../docs/terminology.md#2-triples) changes: each labeling batch depends on the [labels](../docs/terminology.md#5-learning-the-schema-step-040) chosen before it. That's a few dozen [model calls](../docs/terminology.md#8-the-pipeline), not one per text.
- **The labels depend a little on the order component instances are labeled in.** Most common first, so the order is meaningful, not arbitrary, but a different order could coin a different first label for an idea.
- **One call per [kind](../docs/terminology.md#3-schemas) to merge labels.** Up to 800 labels of one kind; above that the [step](../docs/terminology.md#8-the-pipeline) stops rather than merging in groups where synonyms could miss each other. At that size, labels would first need grouping by meaning (e.g. a local embedding model), which isn't built.
- **The sample reads only the 10 largest maintainers.** 150 texts from the 10 largest [maintainers](../docs/terminology.md#1-records-and-their-text) (91.6% of the catalog's [records](../docs/terminology.md#1-records-and-their-text)). The other 412 maintainers (8.4% of the records) are never read, so an [entity class](../docs/terminology.md#3-schemas) or predicate used only in their records can't enter the schema. Within the 10, each maintainer gives 15 texts, whatever its size. This design (10 maintainers, 15 texts each) is a chosen starting point, not a measured optimum; other designs can be compared with it (`helpers/compare_runs.md`). 070's [recall upper bound](../docs/terminology.md#7-evaluating-extraction-step-070) shows whether what was missed matters for the [ground truth](../docs/terminology.md#4-ground-truth-and-samples).
- **min_support is not yet chosen.** It is 1 (keep everything). To choose it: run 040, 060, and 070 with other values and compare the **[tuning part](../docs/terminology.md#7-evaluating-extraction-step-070)'s** metrics, never the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070)'s (see `070_evaluate/070_evaluate.md`). How to weigh [precision](../docs/terminology.md#7-evaluating-extraction-step-070) against [recall](../docs/terminology.md#7-evaluating-extraction-step-070) when choosing is still open.
- **The model varies.** Rerunning with an empty cache can give different [triple instances](../docs/terminology.md#2-triples), labels, and definitions; the cache is what makes a rerun reproducible.
