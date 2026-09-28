# 040_induce_schema

## Purpose

Learns the graph's vocabulary from the catalog itself, instead of writing it in advance:

- **classes**: the kinds of things the texts talk about, e.g. `Instrument`, `Spacecraft`;
- **predicates**: the relations between them, e.g. `ABOARD`;
- **patterns**: which classes each predicate joins, e.g. `Instrument ABOARD Spacecraft`.

A model reads a sample of texts and lists their facts with no schema imposed, gives every name a general label, and merges labels that mean the same thing. Code counts how many texts, and how many maintainers, back each entry, and keeps every entry with that evidence. The schema is judged downstream: 070 measures how much of the ground truth it can express (its schema ceiling) and how well extraction does with it.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | 020's cleaned records: the texts. |
| `splits` | `030_split/splits.json` | 030's induction candidates: every maintainer's records that may be learned from, each maintainer's in a fixed random order. |
| `hand_schema` | `./annotations/schema_derived_from_manual_annotation.txt` (in Git) | The hand-built schema, written while annotating ground truth. Only compared with, in the report; it doesn't shape the induced schema. |

## Outputs

In `outputs/intermediate_results/040_induce_schema/`:

| File | Contents |
|---|---|
| `the_schema.json` | The schema: classes, predicates and patterns, each with its evidence; and what was deferred, with why. |
| `induction_evidence.json` | Everything the schema was built from: each text's verified facts and the facts left out as unverified (with why), every name's label, the labeling batches, every merge and spelling fold, all counts (including entries not in the schema), the definitions, the calls made, and the comparison with the hand-built schema. |
| `cache/` | Every model answer, so a rerun pays only for what changed (see How to run). Not listed in the manifest. |
| `_manifest.json` | Run id, settings, input files and their hashes, output hashes, headline numbers. Written when a run finishes. |

`the_schema.json`, shortened:

```json
{"classes": [{"name": "Instrument", "definition": "A device that takes measurements.",
              "examples": ["MODIS", "AIRS", "CERES"], "support": 34,
              "maintainers": ["Earthdata Forum", "…"], "texts": ["…"],
              "_origin": ["020_clean/records.jsonl#…", "…"]}, …],
 "predicates": [{"name": "ABOARD", "definition": "…", "support": 21, "maintainers": ["…"],
                 "texts": ["…"], "_origin": ["…"]}, …],
 "patterns": [{"pattern": ["Instrument", "ABOARD", "Spacecraft"], "support": 19,
               "maintainers": ["…"], "texts": ["…"], "_origin": ["…"]}, …],
 "deferred": [{"kind": "classes", "candidate": "Thing", "support": 40, "reason": "too vague: …"}, …],
 "made": {"run_id": "040_induce_schema_…", "model": "…", "settings": {…}, "texts": 150,
          "maintainers": ["…"]}}
```

| Field | Meaning |
|---|---|
| `support` | How many different texts produced the entry. |
| `maintainers` | The maintainers those texts came from. Support from many is a catalog-wide regularity; support from one may be that maintainer's house style. |
| `texts`, `_origin` | The records whose texts produced it (see `instructions/000_audit.md`). |
| `examples` | Classes only: the names that most often got the class, picked by code. |
| `deferred` | Everything found but not in the schema: support below `min_support`, judged too vague by the model, or a pattern through an entry not in the schema. |

Each run also leaves `outputs/reports/<run id>.md` and `outputs/logs/<run id>.log`.

## Settings

| Setting | Default | Meaning | When to change it |
|---|---|---|---|
| `induction_maintainers` | 10 | Learn from this many of the largest maintainers. | To cover more (or fewer) of the catalog's maintainers. |
| `texts_per_maintainer` | 15 | Take the first this-many induction candidates of each. | To learn from more text. Taking more keeps the texts already taken, so their extraction calls are reused (see How to run). |
| `min_support` | 1 | An entry enters the schema if found in at least this many texts. 1 keeps everything found. | To be chosen later from 070's scores; see Known limits. |
| `max_chars` | 8000 | A text longer than this is split into pieces, one call each (`common/chunking.py`). | Rarely. No induction text of the default sample is that long (the longest is 5,797 characters). |
| `workers` | 4 | Model calls made at the same time, while extracting facts. | Lower it if the model service starts refusing calls. |
| `confirm_paid_calls` | true | Stop and ask before the first paid call. | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

## How to run

From the repo root, with the environment active, on a computer that can reach Ask Sage (`api.asksage.ai.nasa.gov`), with `ASKSAGE_EMAIL` and `ASKSAGE_API_KEY` in `.env`:

```
py 040_induce_schema.py                                  learn from 150 texts; asks before paying
py 040_induce_schema.py --texts_per_maintainer 30        learn from more text
py 040_induce_schema.py --confirm_paid_calls false       don't ask (unattended runs)
py 040_induce_schema.py --help                           list inputs and settings
```

**Paying.** Before its first paid call, 040 logs its plan (how many extraction calls, the model) and waits: Enter starts, anything else stops the run having spent nothing. Its first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Calls made: about one per text to extract facts, plus a few dozen to label, merge and define; the report counts each stage's calls exactly.

**The cache.** Every model answer is kept in `cache/`, under a fingerprint of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged:

- a failed call isn't kept, so a rerun asks only the calls that failed;
- taking more texts (`texts_per_maintainer`, `induction_maintainers`) reuses every text's extraction already made and pays only for the new texts;
- editing a prompt file asks again exactly the calls that use that prompt;
- deleting `cache/` (or all of `outputs/`) means paying for every call again.

The prompts are plain text files in `040_induce_schema/prompts/`: `extract.txt`, `label_entities.txt`, `label_predicates.txt`, `merge_classes.txt`, `merge_predicates.txt`, `define_classes.txt`, `define_predicates.txt`. `$name` marks where the code fills something in.

## How it works

The step has seven stages. Stages 2, 3, 4 and 6 ask the model; 1, 5 and 7 are code.

1. **Pick the texts** (`texts.py`). From 030's induction candidates, the first `texts_per_maintainer` records of each of the `induction_maintainers` largest maintainers: 150 texts by default. Each text is the record's title and notes (and any extra text fields 020 kept), split into pieces only if it's longer than `max_chars`, with the title repeated at the top of each piece.
2. **Extract facts, and check them** (`extract.py`). One call per text piece: list every fact the text states as subject, predicate and object, in the text's own words ("MODIS -- is aboard -- Aqua"), each with its `source_text`, the passage that states it, copied word for word. Nothing tells the model what kinds of things or relations to look for. Then code checks every fact against the record's whole text (`common/validate.py`, shared with 050 and 060):
   - **left out** (can't be verified, may be invented): a fact with no passage, or whose passage isn't in the text. It counts toward nothing in the later stages, and is listed with why in `induction_evidence.json`;
   - **kept, flagged**: a fact whose subject or object isn't in the text or in its own passage (usually a reworded name, "the instrument" for "MODIS"), or whose subject and object are the same name. The flags are counted in the report.

   "In the text" ignores case, spacing, quote marks, dash styles and a leading "the"/"a"/"an" (`common/text_match.py`). A fact two pieces of one text both state counts once; an item that isn't a complete fact is dropped and counted.
3. **Label every name, with a running vocabulary** (`label.py`). Every subject and object gets a class label ("MODIS" → `Instrument`), and every predicate a predicate label ("is aboard" → `ABOARD`), each judged by the shortest fact it appears in. The names go to the model in batches of 80, most common names first, and every batch is shown the labels chosen so far, with the instruction to reuse one whenever it fits and coin a new one only when none does. So one idea doesn't end up under several labels because its names were in different batches. A name left unlabeled is asked once more; if still unlabeled, it's listed and counts toward nothing.
4. **Merge synonymous labels** (`merge.py`). A few synonyms can still slip through stage 3, so the finished list of labels goes to the model in one call per kind (class labels, predicate labels), each with the names that most often got it. Every label is seen beside every other. The model lists only the merges it finds (`Sensor` → `Instrument`); predicates pointing in opposite directions are never merged. Code checks the reply: a merge must go into a label that was sent; labels that weren't sent are ignored; a label merged twice keeps the first merge; chains are followed to their end. Every merge is listed in the report.
5. **Count the evidence** (`count.py`, code). Each fact becomes, through its labels, a class for its subject and object, a predicate, and, if all three are labeled, a pattern. For every class, predicate and pattern: how many different texts produced it, which texts, and which maintainers. Labels that differ only in case, spacing or punctuation are folded into one first (digits are kept: `Level2` and `Level3` stay apart); every fold is listed.
6. **Write definitions** (`define.py`). Every class and predicate with enough support goes to the model, 40 at a time, for one defining sentence each, or a reason if it's too vague to tell anything apart ("Thing"). This stage only writes words; it merges and chooses nothing.
7. **Build and check the schema** (`check.py`, code). The schema is built from stage 5's counts, never from the model's replies: a class or predicate is in it if its support reaches `min_support` and it isn't too vague; a pattern is in it if its support reaches `min_support` and its two classes and predicate are in it. Everything else is deferred, with its reason. An entry missing its definition stays in, marked, and is listed.

Then, for the report only, **the induced schema is put beside the hand-built one** (`compare.py`, code): which classes, predicates and patterns both have, which only the hand-built one has, and which only the induced one has. Names match when equal ignoring case, spaces and punctuation, so a concept the two name differently (`Instrument`, `Sensor`) counts as unmatched. It's a sanity check on what the data taught the model, not a score: 070 measures how much of the ground truth the schema can express.

The code is in `040_induce_schema/`: `moves.py` (the moves, and writing the results), one file per stage (above), `compare.py`, `cache.py` (the answer cache), and `prompts/`. The hand-built schema is read by `common/schema_io.py`.

### Why "undefined" is one of the maintainers learned from

989 records have no maintainer; 020 files them under `undefined`, a value the catalog itself also uses, and it is the 5th largest maintainer, so it is one of the 10 learned from. Learning from each large maintainer separately is meant to show this step the vocabulary of as much of the catalog as possible; that doesn't need each group to share one writing style. Replacing `undefined` with the next largest maintainer (Christopher Rumsey, 178 records) would cover 0.5% of the catalog instead of 2.7%. (Details in `instructions/030_split.md`.)

## Checks and warnings

| Message | Meaning | What to do |
|---|---|---|
| *N text pieces failed extraction* | Those calls failed (after the model client's own retries); their facts are missing. | Rerun: only the failed pieces are asked again. |
| *N texts gave no facts at all* | The model found no facts in them. | Look at the texts; usually very short records. |
| *N names were left unlabeled even after a second try* | The model skipped them twice. They count toward no class or predicate. | Nothing, if few. Listed in `induction_evidence.json` under `unlabeled`. |
| *The merge reply had items code ignored* | The model proposed a merge into a name that isn't a label, or named labels it wasn't sent. | Nothing: they were ignored. Listed under `merge_issues`. |
| *N schema entries have no definition* | The model didn't define them. They stay in the schema, marked. | Delete `cache/define.json` and rerun to ask again. |
| *The definition replies named N entries that weren't sent* | Ignored. | Nothing. |
| *… labels are more than one call takes* (the step stops) | Over 800 labels of one kind: too many to merge in one call. | See Known limits. |
| *… must be at least 1* (the step stops) | A setting is 0 or less (`max_chars` under 1,000). | Fix the setting. |
| *Test call to … failed* (the step stops) | The model name or the key is wrong, or Ask Sage can't be reached. Nothing else was called. | Check `.env`, `MODEL` in `common/llm.py`, and the network. |
| *Cancelled. Nothing was spent.* (the step stops) | You declined at the confirmation. | — |

## Human work

**Review the merges** listed in the report (and every spelling fold). A wrong merge, two different ideas made one, is the one mistake code can't catch: it just looks like a single, well-supported class.

## Known limits

- **Not yet run with the real model.** As of 2026-09-28, 040 has been tested only with a stand-in for the model, because Ask Sage can't be reached from the laptop it was built on. The numbers in this guide are from the stand-in, the catalog, or the code, not from a real run.
- **Adding texts relabels.** Taking more texts reuses every extraction already made, but labeling (stage 3), merging (4) and definitions (6) are asked again when the set of names changes: each labeling batch depends on the labels chosen before it. That's a few dozen calls, not one per text.
- **The labels depend a little on the order names are labeled in.** Most common names go first, so the order is meaningful, not arbitrary, but a different order could coin a different first label for an idea.
- **One call per kind to merge labels.** Up to 800 labels of one kind; above that the step stops rather than merging in groups where synonyms could miss each other. At that size, labels would first need grouping by meaning (e.g. a local embedding model), which isn't built.
- **What the sample can see.** 150 texts from the 10 largest maintainers (91.6% of the catalog's records). A class used by 1% of the catalog's records is found in the sample with probability 78%; by 0.5%, 53%. 070's schema ceiling shows whether what was missed matters for the ground truth.
- **min_support is not yet chosen.** It is 1 (keep everything) until 070 exists; how to choose it without flattering the scores is decided there.
- **The model varies.** Rerunning with an empty cache can give different facts, labels and definitions; the cache is what makes a rerun reproducible.
