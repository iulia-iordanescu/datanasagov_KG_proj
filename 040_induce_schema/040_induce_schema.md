# 040_induce_schema

Terms ([triple instance](../docs/terminology.md#2-triples), [component instance](../docs/terminology.md#2-triples), [label](../docs/terminology.md#5-learning-the-schema-step-040), [support](../docs/terminology.md#5-learning-the-schema-step-040), …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Learning the schema (step 040)*.

## Purpose

Learns the [schema](../docs/terminology.md#3-schemas) from the catalog itself, instead of writing it in advance:

- **[entity classes](../docs/terminology.md#3-schemas)**: the kinds of things the [texts](../docs/terminology.md#1-records-and-their-text) talk about, e.g. `Instrument`, `Spacecraft`;
- **[predicates](../docs/terminology.md#3-schemas)**: the relations between them, e.g. `ABOARD`;
- **[patterns](../docs/terminology.md#3-schemas)**: which entity classes each predicate joins, e.g. `Instrument ABOARD Spacecraft`.

A [model](../docs/terminology.md#8-the-pipeline) reads a sample of texts and lists the [triple instances](../docs/terminology.md#2-triples) they state, with no schema imposed; code keeps only those it can verify in the text. The model gives every [component instance](../docs/terminology.md#2-triples) a [label](../docs/terminology.md#5-learning-the-schema-step-040) and merges labels that mean the same thing. Code counts the [support](../docs/terminology.md#5-learning-the-schema-step-040) of each [schema entry](../docs/terminology.md#3-schemas) (how many texts, and how many [maintainers](../docs/terminology.md#1-records-and-their-text), back it), and keeps every schema entry with that [evidence](../docs/terminology.md#5-learning-the-schema-step-040). The schema is judged downstream: 070 measures how much of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) it can express (its [recall upper bound](../docs/terminology.md#7-evaluating-extraction-step-070)) and how well extraction does with it.

## To do

### Every step

- **Run it** after the [steps](../docs/terminology.md#8-the-pipeline) before it, and again whenever their outputs change (see *How to run*).
- **Before a step pays for [model calls](../docs/terminology.md#8-the-pipeline),** read what it prints: anything it can't do exactly as asked is listed above the question. Then press Enter to go ahead, or anything else to stop, having spent nothing. (Steps that call no [model](../docs/terminology.md#8-the-pipeline) don't ask.)
- **Read the [report](../docs/terminology.md#8-the-pipeline)'s Warnings:** the report is `outputs/reports/<step>_<date>_<time>.md` (the step prints its path when it ends). Each warning is explained, with what to do, in *Checks and warnings* below.
- **Commit every changed file in the `annotations/` folder to Git,** so your work is safe.

### This step

- **Before the real [run](../docs/terminology.md#8-the-pipeline), choose the [model](../docs/terminology.md#8-the-pipeline):** the strongest one Ask Sage lets you use (`docs/running_on_nasa_laptop.md`, *Choosing a model*).
- **Review the merges** listed in the [report](../docs/terminology.md#8-the-pipeline) (`outputs/reports/040_induce_schema_<date>_<time>.md`, section *Triple instances and labels*), and the spelling folds in `outputs/intermediate_results/040_induce_schema/induction_evidence.json` (under `spelling_folds`). A wrong merge (two different ideas made one) is the one mistake code can't catch: it just looks like a single [entity class](../docs/terminology.md#3-schemas) with high [support](../docs/terminology.md#5-learning-the-schema-step-040).

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned [records](../docs/terminology.md#1-records-and-their-text): the [texts](../docs/terminology.md#1-records-and-their-text). |
| `splits` | `030_split/splits.json` | 030's [induction candidates](../docs/terminology.md#4-ground-truth-and-samples): every [maintainer](../docs/terminology.md#1-records-and-their-text)'s records that may be learned from, each maintainer's in a fixed random order. |
| `hand_schema` | `./annotations/schema_derived_from_manual_annotation.txt` (in Git) | The [hand-built schema](../docs/terminology.md#3-schemas), written while annotating [ground truth](../docs/terminology.md#4-ground-truth-and-samples). Only compared with, in the [report](../docs/terminology.md#8-the-pipeline); it doesn't shape the [induced schema](../docs/terminology.md#5-learning-the-schema-step-040). |

## Outputs

In `outputs/intermediate_results/040_induce_schema/`:

**On a rerun:** both files are replaced; `cache/` keeps every answer, so only calls not asked before are paid.

| File | Contents |
|---|---|
| `the_schema.json` | The [schema](../docs/terminology.md#3-schemas): [entity classes](../docs/terminology.md#3-schemas), [predicates](../docs/terminology.md#3-schemas) and [patterns](../docs/terminology.md#3-schemas), each with its [evidence](../docs/terminology.md#5-learning-the-schema-step-040); and every [schema entry](../docs/terminology.md#3-schemas) [deferred](../docs/terminology.md#5-learning-the-schema-step-040), with why. |
| `induction_evidence.json` | Everything the schema was built from: each [text](../docs/terminology.md#1-records-and-their-text)'s `describes_class`, its [verified triple instances](../docs/terminology.md#2-triples) and the ones left out as unverified (with why), every [component instance](../docs/terminology.md#2-triples)'s [label](../docs/terminology.md#5-learning-the-schema-step-040), the labeling batches, every merge and spelling fold, all counts (including schema entries not in the schema), the definitions, the [model calls](../docs/terminology.md#8-the-pipeline) made, and the comparison with the [hand-built schema](../docs/terminology.md#3-schemas). |
| `cache/` | Every [model](../docs/terminology.md#8-the-pipeline) answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the [manifest](../docs/terminology.md#8-the-pipeline). |
| `_manifest.json` | Run id, [settings](../docs/terminology.md#8-the-pipeline), input files and their hashes, output files and their hashes, headline numbers and the [harvest](../docs/terminology.md#1-records-and-their-text) date. Written when a [run](../docs/terminology.md#8-the-pipeline) finishes. |

`the_schema.json`, shortened:

```json
{"entity_classes": [{"component_class": "Instrument", "definition": "A device that takes measurements.",
                     "examples": ["MODIS", "AIRS", "CERES"], "support": 34,
                     "maintainers": ["Earthdata Forum", "…"], "texts": ["…"],
                     "_origin": ["020_clean/records.jsonl#…", "…"]}, …],
 "predicates": [{"component_class": "ABOARD", "definition": "…", "support": 21, "maintainers": ["…"],
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
| `examples` | Entity classes only: the component instances that most often got the entity class, picked by code. |
| `deferred` | Every schema entry found but not in the schema: support below `min_support`, judged too vague by the model, or a pattern through a schema entry that isn't in the schema. |

Each run also leaves `outputs/reports/<run id>.md` (the [report](../docs/terminology.md#8-the-pipeline): what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `induction_maintainers` | 10 | Learn from this many of the largest [maintainers](../docs/terminology.md#1-records-and-their-text). | To cover more (or fewer) of the catalog's maintainers. |
| `texts_per_maintainer` | 15 | Take the first this-many [induction candidates](../docs/terminology.md#4-ground-truth-and-samples) of each. | To learn from more [text](../docs/terminology.md#1-records-and-their-text). Taking more keeps the texts already taken, so their extraction calls are reused (see How to run). |
| `min_support` | 1 | A [schema entry](../docs/terminology.md#3-schemas) enters the [schema](../docs/terminology.md#3-schemas) if its [support](../docs/terminology.md#5-learning-the-schema-step-040) is at least this. 1 keeps everything found. | Once 070's metrics can compare values; see Known limits. |
| `max_chars` | 8000 | A text longer than this is split into [text pieces](../docs/terminology.md#1-records-and-their-text), one [model call](../docs/terminology.md#8-the-pipeline) each (`common/common_helpers/chunking.py`). | Rarely. No text of the default sample is that long (the longest is 5,797 characters). |
| `workers` | 4 | Model calls made at the same time. | Lower it if Ask Sage refuses calls for coming too fast. |
| `model` | google-claude-sonnet-5 | The AI [model](../docs/terminology.md#8-the-pipeline) to ask. `py helpers/models.py` lists the models Ask Sage shows your account; a listed one may still refuse you, which the [run](../docs/terminology.md#8-the-pipeline)'s first call (the one-line test) finds out for the price of that call. Every cached answer is tied to its model: another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `confirm_paid_calls` | true | Stop and ask before the first model call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), on a computer that can reach Ask Sage and has your key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 040_induce_schema/run.py --help                           every input and setting, with its default
py 040_induce_schema/run.py                                  learn from 150 texts; asks before paying
py 040_induce_schema/run.py --texts_per_maintainer 30        learn from more text
py 040_induce_schema/run.py --confirm_paid_calls false       don't ask (unattended runs)
```

**Paying.** Before its first [model call](../docs/terminology.md#8-the-pipeline), 040 logs its plan (how many extraction calls, the [model](../docs/terminology.md#8-the-pipeline)) and waits: Enter starts, anything else stops the [run](../docs/terminology.md#8-the-pipeline) having spent nothing. If the run can't do exactly what you asked, it says so first, above the question (*Before you pay: this run can't do exactly what you asked*, then the reasons, listed under *Checks and warnings*). Its first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: about one per [text](../docs/terminology.md#1-records-and-their-text) to extract [triple instances](../docs/terminology.md#2-triples), plus a few dozen to [label](../docs/terminology.md#5-learning-the-schema-step-040), merge and define; the [report](../docs/terminology.md#8-the-pipeline) counts each [stage](../docs/terminology.md#8-the-pipeline)'s calls exactly.

**The cache.** Every model answer is kept in `cache/`, under a [fingerprint](../docs/terminology.md#8-the-pipeline) of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed; editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again. Taking more texts (`texts_per_maintainer`, `induction_maintainers`) reuses every text's extraction already made and pays only for the new texts.

## How it works

Seven [stages](../docs/terminology.md#8-the-pipeline), in `040_induce_schema/run.py`'s `main()`; stages 2, 3, 4 and 6 ask the [model](../docs/terminology.md#8-the-pipeline), the others are code:

1. **Pick the [texts](../docs/terminology.md#1-records-and-their-text)** (`texts.py`, `pick_texts`). From 030's [induction candidates](../docs/terminology.md#4-ground-truth-and-samples), the first `texts_per_maintainer` [records](../docs/terminology.md#1-records-and-their-text) of each of the `induction_maintainers` largest [maintainers](../docs/terminology.md#1-records-and-their-text): 150 texts by default. Each text is the record's title and notes (and any extra text [fields](../docs/terminology.md#1-records-and-their-text) 020 kept), split into [text pieces](../docs/terminology.md#1-records-and-their-text) only if it's longer than `max_chars`, with the title repeated at the top of each piece.
2. **Extract [triple instances](../docs/terminology.md#2-triples), and check them** (`extract.py`, `extract_triple_instances`). One [model call](../docs/terminology.md#8-the-pipeline) per text piece: list every [fact](../docs/terminology.md#2-triples) the text states as a triple instance, with the text's own words as its [subject instance](../docs/terminology.md#2-triples) and [object instance](../docs/terminology.md#2-triples) and a short verb phrase in the model's words as its [predicate instance](../docs/terminology.md#2-triples) ("MODIS" – "is aboard" – "Aqua"), each with its [source text](../docs/terminology.md#1-records-and-their-text), copied word for word. Nothing tells the model what kinds of things or relations to look for. The reply also names `describes_class`: the kind of thing the text's title names ("Dataset", "WebTool", …), judged from the whole text; the first piece to name one decides it. [Steps](../docs/terminology.md#8-the-pipeline) 050 and 060 need such [entity classes](../docs/terminology.md#3-schemas) for every record's [DESCRIBES row](../docs/terminology.md#2-triples), so this makes sure the [schema](../docs/terminology.md#3-schemas) has them. Then code checks every triple instance against its record's whole text (`common/common_helpers/validate.py`, shared with 050 and 060):
   - **unverified, left out** (may be invented): a triple instance with no source text, or whose source text isn't in the text. It counts toward nothing in the later stages, and is listed with why in `induction_evidence.json`;
   - **verified, flagged**: a triple instance whose subject or object isn't in the text or in its own source text (usually reworded, "the instrument" for "MODIS"), or whose subject and object are the same. The [flags](../docs/terminology.md#2-triples) are counted in the [report](../docs/terminology.md#8-the-pipeline).

   "In the text" means found once [evened out](../docs/terminology.md#2-triples). A triple instance two pieces of one text both state counts once; an item that isn't a triple instance is dropped and counted.
3. **[Label](../docs/terminology.md#5-learning-the-schema-step-040) every [component instance](../docs/terminology.md#2-triples), with a [running vocabulary](../docs/terminology.md#5-learning-the-schema-step-040)** (`label.py`, `label_component_instances`). A subject or object instance gets an entity class label ("MODIS" → `Instrument`); a predicate instance gets a [predicate](../docs/terminology.md#3-schemas) label ("is aboard" → `ABOARD`). Each is judged by the shortest triple instance it appears in. A text's title isn't sent: its label is its `describes_class` from stage 2, and those labels start the entity vocabulary (most common first), so subject and object instances reuse them. The component instances go to the model in batches of 80, most common first, and every batch is shown the labels chosen so far, with the instruction to reuse one whenever it fits and coin a new one only when none does. So one idea doesn't end up under several labels because its component instances were in different batches. One left unlabeled is asked once more; if still unlabeled, it's listed and counts toward no [schema entry](../docs/terminology.md#3-schemas).
4. **Merge synonymous labels** (`merge.py`, `merge_labels`). A few synonyms can still slip through stage 3, so the finished list of labels goes to the model in one call per kind (entity class labels, predicate labels), each label with the component instances that most often got it. Every label is seen beside every other. The model lists only the merges it finds (`Sensor` → `Instrument`); predicates pointing in opposite directions are never merged. Code checks the reply: a merge must go into a label that was sent; labels that weren't sent are ignored; a label merged twice keeps the first merge; chains are followed to their end. Every merge is listed in the report.
5. **Count the [evidence](../docs/terminology.md#5-learning-the-schema-step-040)** (`count.py`, `count_support`). Each [verified triple instance](../docs/terminology.md#2-triples) becomes, through the labels of its component instances, a subject class, an object class, a predicate, and, if all three are labeled, a [pattern](../docs/terminology.md#3-schemas). Each text's title also counts once toward its label, as an entity class, whether or not it is in a triple instance. For every schema entry: its [support](../docs/terminology.md#5-learning-the-schema-step-040), which texts, and which maintainers. Labels that differ only in case, spacing or punctuation are folded into one first (digits are kept: `Level2` and `Level3` stay apart); every fold is listed in `induction_evidence.json` (the report shows the first 20).
6. **Write definitions** (`define.py`, `write_definitions`). Every entity class and predicate whose support reaches `min_support` goes to the model, 40 at a time, for one defining sentence each, or a reason if it's too vague to tell anything apart ("Thing"). This stage only writes words; it merges and chooses nothing.
7. **Build the schema** (`check.py`, `check_schema`). The schema is built from stage 5's counts, never from the model's replies: an entity class or predicate is in it if its support reaches `min_support` and it isn't too vague; a pattern is in it if its support reaches `min_support` and its two entity classes and its predicate are in it. Every other schema entry is [deferred](../docs/terminology.md#5-learning-the-schema-step-040), with its reason. A schema entry missing its definition stays in, marked, and is listed.

Then, for the report only, **the [induced schema](../docs/terminology.md#5-learning-the-schema-step-040) is put beside the hand-built one** (`compare.py`, code, comparing [component classes](../docs/terminology.md#3-schemas) with `common/common_helpers/triples_io.component_class_key`): which entity classes, predicates and patterns both have, which only the hand-built one has, and which only the induced one has. Component classes match when they are a [loose match](../docs/terminology.md#3-schemas), so a concept the two name differently (`Instrument`, `Sensor`) counts as unmatched. It's a sanity check on what the data taught the model, not a metric: 070 measures how much of the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) the schema can express.

**Then the results** (`results`): `the_schema.json` and `induction_evidence.json` are written; the report.

The code: `040_induce_schema/` holds `run.py` (the [control panel](../docs/terminology.md#8-the-pipeline): inputs, [settings](../docs/terminology.md#8-the-pipeline) and the [moves](../docs/terminology.md#8-the-pipeline), in order); `040_induce_schema/040_induce_schema_helpers/` holds `moves.py` (the moves, and writing the results), one file per stage (above) and `compare.py`; `040_induce_schema/040_induce_schema_prompts/` holds the prompts (see *Prompts*). Shared with other steps: `common/common_helpers/validate.py` and `common/common_helpers/text_match.py` (the checks), `common/common_helpers/schema_io.py` (reading the [hand-built schema](../docs/terminology.md#3-schemas)), `common/common_helpers/chunking.py` (text pieces), `common/common_helpers/cache.py` (the answer cache), `common/common_helpers/llm.py` (the model).

**Why "undefined" is one of the maintainers learned from:** it is the 5th largest (989 records with no maintainer); see `030_split/030_split.md`, *Why "undefined" counts as a maintainer*.

## Prompts

In `040_induce_schema/040_induce_schema_prompts/`:

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `extract.txt` | [stage](../docs/terminology.md#8-the-pipeline) 2, one call per [text piece](../docs/terminology.md#1-records-and-their-text) | list every [fact](../docs/terminology.md#2-triples) the [text](../docs/terminology.md#1-records-and-their-text) states as subject, [predicate](../docs/terminology.md#3-schemas), object, each with its [source text](../docs/terminology.md#1-records-and-their-text) copied word for word; and name the kind of thing the title names (`describes_class`) |
| `label_entity_instances.txt` | stage 3, 80 per call | give each subject or object a general [label](../docs/terminology.md#5-learning-the-schema-step-040) ("MODIS" → `Instrument`), reusing the labels chosen so far |
| `label_predicate_instances.txt` | stage 3, 80 per call | give each predicate a general label ("is aboard" → `ABOARD`), reusing the labels chosen so far |
| `merge_entity_classes.txt` | stage 4, one call | list the [entity class](../docs/terminology.md#3-schemas) labels that mean the same thing |
| `merge_predicates.txt` | stage 4, one call | list the predicate labels that mean the same thing (never ones pointing in opposite directions) |
| `define_entity_classes.txt` | stage 6, 40 per call | write one defining sentence per entity class, or say it's too vague |
| `define_predicates.txt` | stage 6, 40 per call | write one defining sentence per predicate, or say it's too vague |

Each prompt is a plain text file: open it to read exactly what the [model](../docs/terminology.md#8-the-pipeline) is told. `$name` marks where the code fills something in. The prompts speak plainly to the model ("facts", "subjects and objects", "entity classes"), explaining any term they use. Editing a prompt is allowed: the next [run](../docs/terminology.md#8-the-pipeline) asks again every call that uses it, and pays for them.

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the [report](../docs/terminology.md#8-the-pipeline)'s warnings):

| Message | Meaning | What to do |
|---|---|---|
| *You asked for N texts from each maintainer (texts_per_maintainer), but M maintainer(s) don't have that many* | Those [maintainers](../docs/terminology.md#1-records-and-their-text) have fewer [records](../docs/terminology.md#1-records-and-their-text) to learn from ([induction candidates](../docs/terminology.md#4-ground-truth-and-samples)) than asked for, so fewer [texts](../docs/terminology.md#1-records-and-their-text) are used (each one's count is in the report's *What this run worked on* table). | Nothing, or lower `texts_per_maintainer`. |
| *You asked for N maintainers (induction_maintainers), but only M have records to learn from* | Asked for more maintainers than there are; all of them are used. | Lower `induction_maintainers`. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N text pieces failed extraction* | Those [model calls](../docs/terminology.md#8-the-pipeline) failed (after the [model](../docs/terminology.md#8-the-pipeline) client's own retries); their [triple instances](../docs/terminology.md#2-triples) are missing. | Run the [step](../docs/terminology.md#8-the-pipeline) again: only those are asked again, and every answer already paid for is reused. |
| *N texts gave no verified triple instance* | The model found none, or none it listed could be verified in the text. | Look at the texts and their `unverified` list in the [evidence](../docs/terminology.md#5-learning-the-schema-step-040) file; usually very short records. |
| *N component instances were left unlabeled even after a second try* | The model skipped them twice. They count toward no [schema entry](../docs/terminology.md#3-schemas). | Nothing, if few. Listed in `induction_evidence.json` under `unlabeled`. |
| *The merge reply had items code ignored* | The model proposed a merge into something that isn't a [label](../docs/terminology.md#5-learning-the-schema-step-040), named labels it wasn't sent, merged a label twice, or merged a label into one already merged into it (a cycle: A into B, then B into A). Each time the first merge is kept. | Nothing: they were ignored. Listed in `induction_evidence.json` under `merge_issues`. |
| *N schema entries have no definition* | The model didn't define them. They stay in the [schema](../docs/terminology.md#3-schemas), marked. | Delete `cache/define.json` and rerun to ask again. |
| *The definition replies named N schema entries that weren't sent* | Ignored. | Nothing. Listed under `unknown_schema_entries`. |
| *N of M entity classes (or predicates, or patterns) have no origin, so they can't be traced to the input they came from* | Should never happen: a code change dropped the field that records where each item came from. | Fix the code before using the output. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *… labels are more than one call takes* | Over 800 labels of one [kind](../docs/terminology.md#3-schemas): too many to merge in one call. | See Known limits. |
| *missing input files … (run 020_clean or 030_split first, or pass --records / --splits)* | An input file isn't there: usually an earlier step hasn't run. | Run the steps in order, or pass the file with `--<input>`. |
| *… must be at least N* | A [setting](../docs/terminology.md#8-the-pipeline) is out of range: `induction_maintainers`, `texts_per_maintainer`, `min_support` or `workers` under 1, or `max_chars` under 1,000. | Fix the setting. |
| *induction candidate … is not in 020's records; splits.json and records.jsonl are out of step* | 020 was rerun on a different [harvest](../docs/terminology.md#1-records-and-their-text) after 030 wrote `splits.json`. | Delete 030's `splits.json`, then run `py 030_split/run.py` (it writes the file only once). |
| *model must name a model* | The `model` setting is empty. | Give a model's name (`py helpers/models.py` lists them). |
| *Test call to … failed* | Ask Sage refuses you that model, the key is wrong, or Ask Sage can't be reached. Nothing else was called. | If Ask Sage says the model isn't allowed, choose another (`--model`; `py helpers/models.py` lists them). Otherwise check `.env` and the network. |
| *Cancelled. Nothing was spent.* | You declined at the confirmation. | — |
| *Stopped. Calls not yet started were cancelled. Answers already received are kept in the cache.* | You pressed Ctrl+C while the model calls ran. | Run the step again: the answers already received are reused, not paid for again. |
| *Set ASKSAGE_EMAIL and ASKSAGE_API_KEY (e.g. in .env).* | The Ask Sage credentials aren't set, so no model can be called. | Put them in `.env` (see `docs/running_on_nasa_laptop.md`). |

## Audit trail

- **Prompts.** The [report](../docs/terminology.md#8-the-pipeline)'s *Prompts* section lists every prompt the [run](../docs/terminology.md#8-the-pipeline) filled in, each with a [fingerprint](../docs/terminology.md#8-the-pipeline) (sha256) of its exact text, so the prompt behind any answer is known even if the prompt file was edited later (`_manifest.json` keeps the full fingerprints).
- **[Log](../docs/terminology.md#8-the-pipeline).** `outputs/logs/<run id>.log` records the command line, the [settings](../docs/terminology.md#8-the-pipeline), the git commit, every [model call](../docs/terminology.md#8-the-pipeline)'s retries, each [move](../docs/terminology.md#8-the-pipeline)'s duration, each output file's hash and, on failure, the full traceback.
- **[Origin](../docs/terminology.md#8-the-pipeline).** Each [schema entry](../docs/terminology.md#3-schemas)'s `_origin` names the 020 [records](../docs/terminology.md#1-records-and-their-text) whose [texts](../docs/terminology.md#1-records-and-their-text) it was found in, e.g. `020_clean/records.jsonl#a1b2…`; `induction_evidence.json` keeps every text's [triple instances](../docs/terminology.md#2-triples) and [labels](../docs/terminology.md#5-learning-the-schema-step-040).
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every [step](../docs/terminology.md#8-the-pipeline)'s output to the 010 [batch file](../docs/terminology.md#1-records-and-their-text) and the API request that first returned it (`helpers/audit.md`). An [entity class](../docs/terminology.md#3-schemas) or a [predicate](../docs/terminology.md#3-schemas) of the [schema](../docs/terminology.md#3-schemas) can be traced too: `py helpers/audit.py Instrument`.

## Known limits

- **Not yet run with the real [model](../docs/terminology.md#8-the-pipeline).** As of 2026-09-29, 040 has been tested only with a stand-in for the model, because Ask Sage can't be reached from the laptop it was built on. Numbers in this guide come from the catalog, the code or the stand-in, not from a real [run](../docs/terminology.md#8-the-pipeline).
- **Adding [texts](../docs/terminology.md#1-records-and-their-text) relabels.** Taking more texts reuses every extraction already made, but labeling ([stage](../docs/terminology.md#8-the-pipeline) 3), merging (4) and definitions (6) are asked again when the set of [component instances](../docs/terminology.md#2-triples) changes: each labeling batch depends on the [labels](../docs/terminology.md#5-learning-the-schema-step-040) chosen before it. That's a few dozen [model calls](../docs/terminology.md#8-the-pipeline), not one per text.
- **The labels depend a little on the order component instances are labeled in.** Most common first, so the order is meaningful, not arbitrary, but a different order could coin a different first label for an idea.
- **One call per [kind](../docs/terminology.md#3-schemas) to merge labels.** Up to 800 labels of one kind; above that the [step](../docs/terminology.md#8-the-pipeline) stops rather than merging in groups where synonyms could miss each other. At that size, labels would first need grouping by meaning (e.g. a local embedding model), which isn't built.
- **What the sample can see.** 150 texts from the 10 largest [maintainers](../docs/terminology.md#1-records-and-their-text) (91.6% of the catalog's [records](../docs/terminology.md#1-records-and-their-text)). An [entity class](../docs/terminology.md#3-schemas) used by 1% of the catalog's records is found in the sample with probability 78%; by 0.5%, 53%. 070's [recall upper bound](../docs/terminology.md#7-evaluating-extraction-step-070) shows whether what was missed matters for the [ground truth](../docs/terminology.md#4-ground-truth-and-samples).
- **min_support is not yet chosen.** It is 1 (keep everything). To choose it: run 040, 060 and 070 with other values and compare the **[tuning part](../docs/terminology.md#7-evaluating-extraction-step-070)'s** metrics, never the [held-out part](../docs/terminology.md#7-evaluating-extraction-step-070)'s (see `070_evaluate/070_evaluate.md`). How to weigh [precision](../docs/terminology.md#7-evaluating-extraction-step-070) against [recall](../docs/terminology.md#7-evaluating-extraction-step-070) when choosing is still open.
- **The model varies.** Rerunning with an empty cache can give different [triple instances](../docs/terminology.md#2-triples), labels and definitions; the cache is what makes a rerun reproducible.
