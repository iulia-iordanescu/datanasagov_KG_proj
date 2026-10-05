# 040_induce_schema

Terms (triple instance, component instance, label, support, …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Learning the schema (step 040)*.

## Purpose

Learns the schema from the catalog itself, instead of writing it in advance:

- **entity classes**: the kinds of things the texts talk about, e.g. `Instrument`, `Spacecraft`;
- **predicates**: the relations between them, e.g. `ABOARD`;
- **patterns**: which entity classes each predicate joins, e.g. `Instrument ABOARD Spacecraft`.

A model reads a sample of texts and lists the triple instances they state, with no schema imposed; code keeps only those it can verify in the text. The model gives every component instance a label and merges labels that mean the same thing. Code counts the support of each schema entry (how many texts, and how many maintainers, back it), and keeps every schema entry with that evidence. The schema is judged downstream: 070 measures how much of the ground truth it can express (its schema ceiling) and how well extraction does with it.

## To do

### Every step

- **Run it** after the steps before it, and again whenever their outputs change (see *How to run*).
- **Before a step pays for model calls,** read what it prints: anything it can't do exactly as asked is listed above the question. Then press Enter to go ahead, or anything else to stop, having spent nothing. (Steps that call no model don't ask.)
- **Read the report's Warnings:** the report is `outputs/reports/<step>_<date>_<time>.md` (the step prints its path when it ends). Each warning is explained, with what to do, in *Checks and warnings* below.
- **Commit every changed file in the `annotations/` folder to Git,** so your work is safe.

### This step

- **Before the real run, choose the model:** the strongest one Ask Sage lets you use (`docs/running_on_nasa_laptop.md`, *Choosing a model*).
- **Review the merges** listed in the report (`outputs/reports/040_induce_schema_<date>_<time>.md`, section *Triple instances and labels*), and the spelling folds in `outputs/intermediate_results/040_induce_schema/induction_evidence.json` (under `spelling_folds`). A wrong merge (two different ideas made one) is the one mistake code can't catch: it just looks like a single entity class with high support.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned records: the texts. |
| `splits` | `030_split/splits.json` | 030's induction candidates: every maintainer's records that may be learned from, each maintainer's in a fixed random order. |
| `hand_schema` | `./annotations/schema_derived_from_manual_annotation.txt` (in Git) | The hand-built schema, written while annotating ground truth. Only compared with, in the report; it doesn't shape the induced schema. |

## Outputs

In `outputs/intermediate_results/040_induce_schema/`:

**On a rerun:** both files are replaced; `cache/` keeps every answer, so only calls not asked before are paid.

| File | Contents |
|---|---|
| `the_schema.json` | The schema: entity classes, predicates and patterns, each with its evidence; and every schema entry deferred, with why. |
| `induction_evidence.json` | Everything the schema was built from: each text's `describes_class`, its verified triple instances and the ones left out as unverified (with why), every component instance's label, the labeling batches, every merge and spelling fold, all counts (including schema entries not in the schema), the definitions, the model calls made, and the comparison with the hand-built schema. |
| `cache/` | Every model answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the manifest. |
| `_manifest.json` | Run id, settings, input files and their hashes, output files and their hashes, headline numbers and the harvest date. Written when a run finishes. |

`the_schema.json`, shortened:

```json
{"entity_classes": [{"name": "Instrument", "definition": "A device that takes measurements.",
                     "examples": ["MODIS", "AIRS", "CERES"], "support": 34,
                     "maintainers": ["Earthdata Forum", "…"], "texts": ["…"],
                     "_origin": ["020_clean/records.jsonl#…", "…"]}, …],
 "predicates": [{"name": "ABOARD", "definition": "…", "support": 21, "maintainers": ["…"],
                 "texts": ["…"], "_origin": ["…"]}, …],
 "patterns": [{"pattern": ["Instrument", "ABOARD", "Spacecraft"], "support": 19,
               "maintainers": ["…"], "texts": ["…"], "_origin": ["…"]}, …],
 "deferred": [{"kind": "entity_classes", "name": "Thing", "support": 40, "reason": "too vague: …"}, …],
 "made": {"run_id": "040_induce_schema_…", "model": "…", "settings": {…}, "texts": 150,
          "maintainers": ["…"]}}
```

| Field | Meaning |
|---|---|
| `support` | The schema entry's support: how many different texts it was found in. |
| `maintainers` | The maintainers those texts came from. Support from many is a catalog-wide regularity; support from one may be that maintainer's house style. |
| `texts`, `_origin` | The records whose texts it was found in (see `helpers/audit.md`). |
| `examples` | Entity classes only: the component instances that most often got the entity class, picked by code. |
| `deferred` | Every schema entry found but not in the schema: support below `min_support`, judged too vague by the model, or a pattern through a schema entry that isn't in the schema. |

Each run also leaves `outputs/reports/<run id>.md` (the report: what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `induction_maintainers` | 10 | Learn from this many of the largest maintainers. | To cover more (or fewer) of the catalog's maintainers. |
| `texts_per_maintainer` | 15 | Take the first this-many induction candidates of each. | To learn from more text. Taking more keeps the texts already taken, so their extraction calls are reused (see How to run). |
| `min_support` | 1 | A schema entry enters the schema if its support is at least this. 1 keeps everything found. | Once 070's scores can compare values; see Known limits. |
| `max_chars` | 8000 | A text longer than this is split into text pieces, one model call each (`common/common_helpers/chunking.py`). | Rarely. No text of the default sample is that long (the longest is 5,797 characters). |
| `workers` | 4 | Model calls made at the same time. | Lower it if Ask Sage refuses calls for coming too fast. |
| `model` | google-claude-sonnet-5 | The AI model to ask. `py helpers/models.py` lists the models Ask Sage shows your account; a listed one may still refuse you, which the run's first call (the one-line test) finds out for the price of that call. Every cached answer is tied to its model: another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `confirm_paid_calls` | true | Stop and ask before the first model call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), on a computer that can reach Ask Sage and has your key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 040_induce_schema/run.py --help                           every input and setting, with its default
py 040_induce_schema/run.py                                  learn from 150 texts; asks before paying
py 040_induce_schema/run.py --texts_per_maintainer 30        learn from more text
py 040_induce_schema/run.py --confirm_paid_calls false       don't ask (unattended runs)
```

**Paying.** Before its first model call, 040 logs its plan (how many extraction calls, the model) and waits: Enter starts, anything else stops the run having spent nothing. If the run can't do exactly what you asked, it says so first, above the question (*Before you pay: this run can't do exactly what you asked*, then the reasons, listed under *Checks and warnings*). Its first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: about one per text to extract triple instances, plus a few dozen to label, merge and define; the report counts each stage's calls exactly.

**The cache.** Every model answer is kept in `cache/`, under a fingerprint of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed; editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again. Taking more texts (`texts_per_maintainer`, `induction_maintainers`) reuses every text's extraction already made and pays only for the new texts.

## How it works

Seven stages, in `040_induce_schema/run.py`'s `main()`; stages 2, 3, 4 and 6 ask the model, the others are code:

1. **Pick the texts** (`texts.py`, `pick_texts`). From 030's induction candidates, the first `texts_per_maintainer` records of each of the `induction_maintainers` largest maintainers: 150 texts by default. Each text is the record's title and notes (and any extra text fields 020 kept), split into text pieces only if it's longer than `max_chars`, with the title repeated at the top of each piece.
2. **Extract triple instances, and check them** (`extract.py`, `extract_triple_instances`). One model call per text piece: list every fact the text states as a triple instance, with the text's own words as its component instances ("MODIS" – "is aboard" – "Aqua"), each with its source text, copied word for word. Nothing tells the model what kinds of things or relations to look for. The reply also names `describes_class`: the kind of thing the text's title names ("Dataset", "WebTool", …), judged from the whole text; the first piece to name one decides it. Steps 050 and 060 need such entity classes for every record's DESCRIBES row, so this makes sure the schema has them. Then code checks every triple instance against its record's whole text (`common/common_helpers/validate.py`, shared with 050 and 060):
   - **unverified, left out** (may be invented): a triple instance with no source text, or whose source text isn't in the text. It counts toward nothing in the later stages, and is listed with why in `induction_evidence.json`;
   - **verified, flagged**: a triple instance whose subject or object isn't in the text or in its own source text (usually reworded, "the instrument" for "MODIS"), or whose subject and object are the same. The flags are counted in the report.

   "In the text" ignores case, spacing, quote marks, dash styles and a leading "the"/"a"/"an" (`common/common_helpers/text_match.py`). A triple instance two pieces of one text both state counts once; an item that isn't a triple instance is dropped and counted.
3. **Label every component instance, with a running vocabulary** (`label.py`, `label_component_instances`). A component instance in a subject or object slot gets an entity class label ("MODIS" → `Instrument`); one in a predicate slot gets a predicate label ("is aboard" → `ABOARD`). Each is judged by the shortest triple instance it appears in. A text's title isn't sent: its label is its `describes_class` from stage 2, and those labels start the entity vocabulary (most common first), so other component instances reuse them. The component instances go to the model in batches of 80, most common first, and every batch is shown the labels chosen so far, with the instruction to reuse one whenever it fits and coin a new one only when none does. So one idea doesn't end up under several labels because its component instances were in different batches. One left unlabeled is asked once more; if still unlabeled, it's listed and counts toward no schema entry.
4. **Merge synonymous labels** (`merge.py`, `merge_labels`). A few synonyms can still slip through stage 3, so the finished list of labels goes to the model in one call per kind (entity class labels, predicate labels), each label with the component instances that most often got it. Every label is seen beside every other. The model lists only the merges it finds (`Sensor` → `Instrument`); predicates pointing in opposite directions are never merged. Code checks the reply: a merge must go into a label that was sent; labels that weren't sent are ignored; a label merged twice keeps the first merge; chains are followed to their end. Every merge is listed in the report.
5. **Count the evidence** (`count.py`, `count_support`). Each verified triple instance becomes, through the labels of its component instances, an entity class for its subject and its object, a predicate, and, if all three are labeled, a pattern. Each text's title also counts once toward its label, as an entity class, whether or not it is in a triple instance. For every schema entry: its support, which texts, and which maintainers. Labels that differ only in case, spacing or punctuation are folded into one first (digits are kept: `Level2` and `Level3` stay apart); every fold is listed in `induction_evidence.json` (the report shows the first 20).
6. **Write definitions** (`define.py`, `write_definitions`). Every entity class and predicate whose support reaches `min_support` goes to the model, 40 at a time, for one defining sentence each, or a reason if it's too vague to tell anything apart ("Thing"). This stage only writes words; it merges and chooses nothing.
7. **Build the schema** (`check.py`, `check_schema`). The schema is built from stage 5's counts, never from the model's replies: an entity class or predicate is in it if its support reaches `min_support` and it isn't too vague; a pattern is in it if its support reaches `min_support` and its two entity classes and its predicate are in it. Every other schema entry is deferred, with its reason. A schema entry missing its definition stays in, marked, and is listed.

Then, for the report only, **the induced schema is put beside the hand-built one** (`compare.py`, code, comparing names with `common/common_helpers/triples_io.label_key`): which entity classes, predicates and patterns both have, which only the hand-built one has, and which only the induced one has. Names match when equal ignoring case, spaces and punctuation, so a concept the two name differently (`Instrument`, `Sensor`) counts as unmatched. It's a sanity check on what the data taught the model, not a score: 070 measures how much of the ground truth the schema can express.

**Then the results** (`results`): `the_schema.json` and `induction_evidence.json` are written; the report.

The code: `040_induce_schema/` holds `run.py` (the control panel: inputs, settings and the moves, in order); `040_induce_schema/040_induce_schema_helpers/` holds `moves.py` (the moves, and writing the results), one file per stage (above) and `compare.py`; `040_induce_schema/040_induce_schema_prompts/` holds the prompts (see *Prompts*). Shared with other steps: `common/common_helpers/validate.py` and `common/common_helpers/text_match.py` (the checks), `common/common_helpers/schema_io.py` (reading the hand-built schema), `common/common_helpers/chunking.py` (text pieces), `common/common_helpers/cache.py` (the answer cache), `common/common_helpers/llm.py` (the model).

**Why "undefined" is one of the maintainers learned from:** it is the 5th largest (989 records with no maintainer); see `030_split/030_split.md`, *Why "undefined" counts as a maintainer*.

## Prompts

In `040_induce_schema/040_induce_schema_prompts/`:

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `extract.txt` | stage 2, one call per text piece | list every fact the text states as subject, predicate, object, each with its source text copied word for word; and name the kind of thing the title names (`describes_class`) |
| `label_entity_instances.txt` | stage 3, 80 per call | give each subject or object a general label ("MODIS" → `Instrument`), reusing the labels chosen so far |
| `label_predicate_instances.txt` | stage 3, 80 per call | give each predicate a general label ("is aboard" → `ABOARD`), reusing the labels chosen so far |
| `merge_entity_classes.txt` | stage 4, one call | list the entity class labels that mean the same thing |
| `merge_predicates.txt` | stage 4, one call | list the predicate labels that mean the same thing (never ones pointing in opposite directions) |
| `define_entity_classes.txt` | stage 6, 40 per call | write one defining sentence per entity class, or say it's too vague |
| `define_predicates.txt` | stage 6, 40 per call | write one defining sentence per predicate, or say it's too vague |

Each prompt is a plain text file: open it to read exactly what the model is told. `$name` marks where the code fills something in. The prompts speak plainly to the model ("facts", "names", "classes"), not in this project's terms, which the model doesn't know. Editing a prompt is allowed: the next run asks again every call that uses it, and pays for them.

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the report's warnings):

| Message | Meaning | What to do |
|---|---|---|
| *You asked for N texts from each maintainer (texts_per_maintainer), but M maintainer(s) don't have that many* | Those maintainers have fewer records to learn from (induction candidates) than asked for, so fewer texts are used (each one's count is in the report's *What this run worked on* table). | Nothing, or lower `texts_per_maintainer`. |
| *You asked for N maintainers (induction_maintainers), but only M have records to learn from* | Asked for more maintainers than there are; all of them are used. | Lower `induction_maintainers`. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N text pieces failed extraction* | Those model calls failed (after the model client's own retries); their triple instances are missing. | Run the step again: only those are asked again, and every answer already paid for is reused. |
| *N texts gave no verified triple instance* | The model found none, or none it listed could be verified in the text. | Look at the texts and their `unverified` list in the evidence file; usually very short records. |
| *N component instances were left unlabeled even after a second try* | The model skipped them twice. They count toward no schema entry. | Nothing, if few. Listed in `induction_evidence.json` under `unlabeled`. |
| *The merge reply had items code ignored* | The model proposed a merge into something that isn't a label, named labels it wasn't sent, or merged a label twice (the first merge is kept). | Nothing: they were ignored. Listed in `induction_evidence.json` under `merge_issues`. |
| *N schema entries have no definition* | The model didn't define them. They stay in the schema, marked. | Delete `cache/define.json` and rerun to ask again. |
| *The definition replies named N schema entries that weren't sent* | Ignored. | Nothing. Listed under `unknown_schema_entries`. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *… labels are more than one call takes* | Over 800 labels of one kind: too many to merge in one call. | See Known limits. |
| *missing input files … (run 020_clean or 030_split first, or pass --records / --splits)* | An input file isn't there: usually an earlier step hasn't run. | Run the steps in order, or pass the file with `--<input>`. |
| *… must be at least N* | A setting is out of range: `induction_maintainers`, `texts_per_maintainer`, `min_support` or `workers` under 1, or `max_chars` under 1,000. | Fix the setting. |
| *induction candidate … is not in 020's records; splits.json and records.jsonl are out of step* | 020 was rerun on a different harvest after 030 wrote `splits.json`. | Delete 030's `splits.json`, then run `py 030_split/run.py` (it writes the file only once). |
| *model must name a model* | The `model` setting is empty. | Give a model's name (`py helpers/models.py` lists them). |
| *Test call to … failed* | Ask Sage refuses you that model, the key is wrong, or Ask Sage can't be reached. Nothing else was called. | If Ask Sage says the model isn't allowed, choose another (`--model`; `py helpers/models.py` lists them). Otherwise check `.env` and the network. |
| *Cancelled. Nothing was spent.* | You declined at the confirmation. | — |

## Audit trail

- **Log.** `outputs/logs/<run id>.log` records the command line, the settings, the git commit, every model call's retries, each move's duration, each output file's hash and, on failure, the full traceback.
- **Origin.** Each schema entry's `_origin` names the 020 records whose texts it was found in, e.g. `020_clean/records.jsonl#a1b2…`; `induction_evidence.json` keeps every text's triple instances and labels.
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every step's output to the 010 batch file and the API request that first returned it (`helpers/audit.md`). A schema entry can be traced by its name: `py helpers/audit.py Instrument`.

## Known limits

- **Not yet run with the real model.** As of 2026-09-29, 040 has been tested only with a stand-in for the model, because Ask Sage can't be reached from the laptop it was built on. Numbers in this guide come from the catalog, the code or the stand-in, not from a real run.
- **Adding texts relabels.** Taking more texts reuses every extraction already made, but labeling (stage 3), merging (4) and definitions (6) are asked again when the set of component instances changes: each labeling batch depends on the labels chosen before it. That's a few dozen model calls, not one per text.
- **The labels depend a little on the order component instances are labeled in.** Most common first, so the order is meaningful, not arbitrary, but a different order could coin a different first label for an idea.
- **One call per kind to merge labels.** Up to 800 labels of one kind; above that the step stops rather than merging in groups where synonyms could miss each other. At that size, labels would first need grouping by meaning (e.g. a local embedding model), which isn't built.
- **What the sample can see.** 150 texts from the 10 largest maintainers (91.6% of the catalog's records). An entity class used by 1% of the catalog's records is found in the sample with probability 78%; by 0.5%, 53%. 070's schema ceiling shows whether what was missed matters for the ground truth.
- **min_support is not yet chosen.** It is 1 (keep everything). To choose it: run 040, 060 and 070 with other values and compare the **tuning part's** scores, never the held-out part's (see `070_evaluate/070_evaluate.md`). How to weigh precision against recall when choosing is still open.
- **The model varies.** Rerunning with an empty cache can give different triple instances, labels and definitions; the cache is what makes a rerun reproducible.
