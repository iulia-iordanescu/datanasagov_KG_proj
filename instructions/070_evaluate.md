# 070_evaluate

Terms (precision, recall, match, margin of error, bootstrap, tuning part, held-out part, …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Scoring extraction (step 070)*.

## Purpose

Scores what step 060 extracted against the ground truth, the answer key:

- **precision**: when 060 says something, how often it is right;
- **recall**: of the facts in the ground truth, how many 060 found;

each with its **margin of error**, so a real improvement can be told from luck. Around them:

- **entity-class accuracy**: of the facts 060 got right, how often it also named the kinds of things right;
- **schema ceiling**: how much of the ground truth the schema can express at all, and **recall within reach**: how well 060 did on what it could do. A low ceiling means the schema needs work; a high ceiling with low recall within reach means the extraction does;
- **what each record describes**: how often 060 named the right kind of thing for the DESCRIBES row, next to what always guessing the most common kind would score.

Before comparing, 060's names are translated into the ground truth's names (yours), through a table you check. Only the **fair part** of the ground truth is scored (a fair sample of the catalog), and by default only its **tuning part**: the held-out part is kept for the end.

The ground truth was drafted by a model (050) and corrected by a person, not written from scratch; a fact both missed is counted nowhere, so recall may come out higher than it is. The report says so.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `records` | `020_clean/records.jsonl` | Titles, for the per-record list. |
| `splits` | `030_split/splits.json` | The pool's order, and each record's part (tuning or held-out). |
| `extracted_triples` | `060_extract/extracted_triples.csv` | What 060 kept. |
| `extracted_triples_details` | `060_extract/extracted_triples_details.json` | Which records 060 extracted (a record whose call failed is not scored, not scored as zero). |
| `schema_used` | `060_extract/schema_used.json` | The schema 060 used: the names to translate. |
| `candidates` | `./annotations/ground_truth_candidates.csv` (in Git) | Each pool record's sampling group. |
| `hand_schema` | `./annotations/schema_derived_from_manual_annotation.txt` (in Git) | The hand-built schema: with the names coined in the ground truth, the ground truth vocabulary ("your names" here), built by `common/ground_truth.vocabulary` as in 050 and the annotation tool. |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | The answer key. Only records you've finished (*All facts extracted*) are scored. |
| `name_mapping` | `./annotations/name_mapping.csv` (in Git) | The translation table (below). |

## Outputs

In `outputs/intermediate_results/070_evaluate/`:

**On a rerun:** the three files are replaced; `cache/` keeps every answer; the lines 070 added to `annotations/` stay.

| File | Contents |
|---|---|
| `per_record.md` | For reading. Each scored record of the parts shown (the tuning part; the held-out part too with `--score_held_out true`, so its facts stay unseen until then): what it describes (✓/✗), its facts **matched** (✓ exact or ≈ partial, with the ground truth's version when they differ), **extracted but not in the ground truth** (they count against precision) and **in the ground truth but not extracted** (against recall; marked *out of reach* when the schema can't express them). Extracted facts are shown translated into your names. Opens well in VS Code or on GitHub. |
| `matches.csv` | For sorting and filtering, e.g. in Excel. One row per fact of the parts shown: record, pool position, part, group, `status` (`exact`, `partial`, `wrong`, `missed`), `entity_classes_right`, `within_reach`, then the fact as extracted, as translated, and as in the ground truth, and where each came from (`origin`). |
| `scores.json` | For comparing runs. Every number (each with `value`, `low`, `high`: the margin), per part and per sampling group; which records were scored and which left out, and why; the settings. |
| `cache/` | Every model answer, so a rerun pays only for what isn't there yet (see *How to run*). Not listed in the manifest. |
| `_manifest.json` | Run id, settings, input files and their hashes, output files and their hashes, headline numbers and the harvest date. Written when a run finishes. |

Each run also leaves `outputs/reports/<run id>.md` (the report: what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `instructions/000_audit.md`. The report shows the numbers, the group table and every warning: read it first.

**Two files in `annotations/` that 070 adds to**, the only exceptions to "no step writes into `annotations/`". 070 only ever **adds** lines at their end; a line already there is never changed or deleted:

| File | What 070 adds |
|---|---|
| `annotations/name_mapping.csv` | Rows for names of 060's schema that have none yet (see *How it works*, stage 2). |
| `annotations/held_out_looks.csv` | One line per run with `--score_held_out true`: date, run id, schema used, held-out records scored. Commit it: it's how the looks are counted, across laptops and after `outputs/` is deleted. |

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `score_held_out` | false | Also show the held-out part's numbers, and log the look in `annotations/held_out_looks.csv`. | Only at the end, for the numbers you report. Each look is a chance to tune on the held-out part without meaning to. |
| `model` | google-claude-sonnet-5 | The AI model to ask. `py models.py` lists the models Ask Sage shows your account; a listed one may still refuse you, which the run's first call (the one-line test) finds out for the price of that call. Every cached answer is tied to its model: another model asks everything again, and switching back reuses the earlier answers. | See *Choosing a model* in `docs/running_on_nasa_laptop.md`. |
| `confirm_paid_calls` | true | Stop and ask before the first model call (070 calls the model only to propose translations for names it has no row for). | `false` for runs with nobody at the keyboard, e.g. the whole pipeline. |

The numbers that are fixed on purpose (in `070_evaluate/stats.py`): `MIN_RECORDS = 20` (fewer scored records: no margin), `RESHUFFLES = 1000`, `SEED = 70` (a rerun gives the same margins), `SHARE_GAP = 0.10` (see *Checks and warnings*).

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`), and, when names need translating, on a computer that can reach Ask Sage with your key in `.env` (`docs/running_on_nasa_laptop.md`):

```
py 070_evaluate.py --help                    every input and setting, with its default
py 070_evaluate.py                           the tuning part
py 070_evaluate.py --score_held_out true     also the held-out part (for the end; each look is logged)
py 070_evaluate.py --confirm_paid_calls false    don't ask (unattended runs)
```

Needs 060's output. The first run with a new schema stops after adding rows to `annotations/name_mapping.csv`: check them, then run again.

**Paying.** Before its first model call, 070 logs its plan (how many names to translate, the model) and waits: Enter starts, anything else stops the run having spent nothing. If the run can't do exactly what you asked, it says so first, above the question (*Before you pay: this run can't do exactly what you asked*, then the reasons, listed under *Checks and warnings*). Its first call is a one-line test that the model name and key work. A run whose answers are all in the cache never asks and never pays. Model calls: one, only when 060's schema has names without a row in `annotations/name_mapping.csv`; no call otherwise, since the scoring is code.

**The cache.** Every model answer is kept in `cache/`, under a fingerprint of everything that decided it: the model, the prompt's exact text, and what was sent. A rerun reuses every answer whose fingerprint is unchanged: a failed call isn't kept, so a rerun asks only the calls that failed; editing a prompt asks again exactly the calls that use it; deleting `cache/` (or all of `outputs/`) means paying for every call again.

## How it works

Four stages, in `070_evaluate.py`'s `main()`; stage 2 asks the model (only for names without a row), the others are code:

1. **Pick the records** (`records.py`, `pick_records`). A record is scored if you've finished it in the ground truth and 060's last run extracted it. Of those, only the **fair part**: the longest run of the pool's first records that are all scored. A record after a gap (an unfinished or unextracted pool record before it) or outside the pool is left out and named, so every scored record belongs to a fair sample.
2. **Translate names** (`names.py`, `translate_names`), through `annotations/name_mapping.csv`:

   ```
   kind,name_from_past_or_crt_schema,name_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema
   entity class,Satellite,Spacecraft,no,yes,A craft that orbits a body.
   predicate,CARRIES,ABOARD,yes,yes,Has on board.         "A CARRIES B" is "B ABOARD A"
   entity class,Gadget,(none),no,yes,A small device.      nothing of yours means this
   entity class,Dataset,Dataset,no,same name,A set of data.
   ```

   For each name of 060's schema without a row: one equal to one of yours (ignoring case, spaces and punctuation) gets a row at once, `checked` = `same name`; the model proposes the others (one paid call, after the usual confirmation), `checked` = `no`. The step then stops. You check each `no` row: fix `name_in_gtt` (one of your names, or `(none)`) and `swap_subject_and_object` where wrong, then set `checked` to `yes`. Scoring runs only once every row it needs is checked. Each row also keeps the current schema's definition of its name from when it was written or last checked (`definition_from_past_or_crt_schema`): if a later schema defines that name differently, the row is **stale** (it may no longer be right) and the step stops until you check it again; checking it again stores the new definition. So the one table can serve every schema: a name keeps its row while its meaning stays the same. The model's proposals are only a first draft: in testing, a stand-in's deliberate mistake (`Phase` → `(none)` instead of `MissionPhase`) is exactly what the check is for.
3. **Compare, record by record** (`match.py`, `compare`). Each extracted fact is translated into your names; a reversed predicate also swaps subject and object. Then the ground truth's facts and the extracted facts are **paired**: every fact, in either list, ends with **zero or one partner**, always from the other list (so a fact stated twice earns one match, not two; the two lists can have any lengths). Two rounds, each finding the largest possible set of pairs (*maximum matching*: a pairing may switch to another partner to free one for a fact that would otherwise have none; taking each fact's first match in list order could lose a real match, and make the score depend on the order facts were written in):
   - **exact**: subject and object the same once evened out (case, spacing, quote marks, dashes, edge punctuation and a leading "the/a/an" ignored, as everywhere in the pipeline), predicate the same;
   - **partial**, among the facts still unpaired: the same, except that a subject or object may be contained in the other as whole words: "MODIS" in "Moderate Resolution Imaging Spectroradiometer (MODIS)". This can be fooled ("MODIS" in "MODIS Terra"), which is why every partial pair is listed in `per_record.md`.

   A pair is **strict** when both entity classes also agree. A ground truth fact is **within reach** when its predicate and both its entity classes are names some checked row translates to. The DESCRIBES rows are compared only on their entity class, apart from the facts, since code writes the rest of them.
4. **Score** (`stats.py`, `score`). Every number is summed over the records before dividing (a fact is an answer, whichever record it's in):

   | Number | Is |
   |---|---|
   | precision | facts matched ÷ facts extracted |
   | recall | facts matched ÷ ground truth facts |
   | strict precision, strict recall | the same, counting only strict pairs |
   | entity-class accuracy | strict pairs ÷ pairs |
   | schema ceiling | ground truth facts within reach ÷ all ground truth facts |
   | recall within reach | matched facts within reach ÷ facts within reach |
   | describes: accuracy | records whose DESCRIBES entity class is right ÷ records whose ground truth names one |
   | describes: baseline | the share of the most common kind: what always guessing it would score |
   | describes: per-kind average | each kind's accuracy, averaged, so rare kinds count as much as common ones |

   Each is given at both name levels (**exact**, and **partial**, which counts exact and partial pairs), with its **margin of error** by the **bootstrap** (below), for the tuning part, for the held-out part when asked, and per sampling group. The report adds a table of what 060 said each record describes versus what it is.

**Then the results** (`results`): `scores.json`, `per_record.md` and `matches.csv` are written, replacing the last run's; with `--score_held_out true`, a line is added to `annotations/held_out_looks.csv`; the report.

The code: `070_evaluate/` holds `moves.py` (the moves, and writing the results), `records.py`, `names.py`, `match.py`, `stats.py` and `prompts/`. Shared with other steps: `common/ground_truth.py` (reading the ground truth; the fair part), `common/text_match.py`, `common/triples_io.py`, `common/files.py` (adding lines without changing any), `common/cache.py`, `common/llm.py`.

### The margin of error, and the checks it needs

The bootstrap recomputes every number 1,000 times, each time from records drawn at random from the scored ones, with repeats, and takes the middle 95% of the results. Its conditions, and how 070 checks them:

| Condition | Why | How 070 checks it |
|---|---|---|
| The scored records are a random sample of the catalog | Otherwise the numbers say nothing about the rest of the catalog. | Only the fair part is scored (How it works, 1); anything else is left out and named. |
| Whole records are drawn, not facts | A record's facts come from one text and one model call, so they succeed or fail together; drawing facts one by one gives margins too narrow. | By design. |
| Drawn the way the pool was drawn | The pool was drawn by sampling group, each getting its share. | Each reshuffle draws within each sampling group as many records as it has. A record without a group is left out of the per-group numbers, and named. |
| Enough records | With very few, the margins are themselves unreliable, usually too narrow. | Below 20 records, no margin: a plain warning that the numbers could easily have come out very differently. 20 is a rule of thumb, not a law. |

A margin covers only **which records happened to be scored**: not mistakes in the ground truth, not the model answering differently on another run (the cache holds one answer per question), and not tuning on the scored records (the held-out part is for that).

**Per sampling group**, every group of the pool is listed with its number of scored records, its share of them and its share of the pool; its numbers appear once it has 20 records. Overall numbers need no weighting, because each group had places in proportion to its size. Two more checks:

- if a group's share of the scored records differs from its share of the pool by more than 10 points (with enough records), the report warns: the scored records don't mirror the pool;
- with many groups, about 1 in 20 margins misses the true value by chance, so one group that looks unusually good or bad is not, alone, a finding. The report says so beside the table.

## Prompts

| Prompt file | Sent in | Asks the model to |
|---|---|---|
| `070_evaluate/prompts/map_names.txt` | stage 2, one call, only for names of 060's schema without a row | for each of those names, give the one of yours that means the same thing (or none), and say whether a predicate states the relation in the opposite direction; your names and their definitions are shown in the prompt |

Each prompt is a plain text file: open it to read exactly what the model is told. `$name` marks where the code fills something in. The prompts speak plainly to the model ("facts", "names", "classes"), not in this project's terms, which the model doesn't know. Editing a prompt is allowed: the next run asks again every call that uses it, and pays for them. Its answers are only proposals: you check every row before scoring uses it.

## Checks and warnings

**Shown before paying**, above the confirmation question (and also in the report's warnings):

| Message | Meaning | What to do |
|---|---|---|
| *N finished ground truth record(s) weren't extracted by 060's last run* | They can't be scored. | Run `py 060_extract.py`. |
| *N record(s) are left out because they aren't in the fair part* | A pool record before them isn't finished or extracted, or they're outside the pool. | Finish (or extract) the records before them. |
| *N scored record(s) have no sampling group* | Not in the pool file. | Normally impossible for pool records. |
| *Ground truth: record … is in batch_… and batch_…: annotated twice* | A record is annotated twice. It's left out of the ground truth until fixed. | Keep it in one file. |
| *Ground truth: record … all_facts_extracted is 0 on some rows, 1 on others* | Mixed, so the record doesn't count as finished. | Set it the same on every row (the tool's box does). |
| *Ground truth: batch_… lacks the column(s) …; not read* | A ground truth file without one of the columns (see `annotations/README.md`). | Add the column. |

**In the report**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *only N record(s) scored, fewer than 20* | No margin of error; don't draw conclusions yet. | Annotate more; until then, read `per_record.md` rather than the numbers. |
| *some sampling group's share … differs from its share of the pool* | The scored records don't mirror the pool. | Look at the group table; usually hand-picked or skipped records. |
| *The held-out part was looked at: N time(s) so far* | After `--score_held_out true`: each look is logged and counted. | Commit `annotations/held_out_looks.csv`. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *Added N row(s) to name_mapping.csv …* | New names of 060's schema. | Check the rows with `checked` = `no` (easiest in `py annotate.py`, *Translation table*), then run again. |
| *N checked row(s) of name_mapping.csv were checked when the current schema defined the name differently* | A later schema uses the name, but defines it differently from when the row was checked: the translation may no longer be right. | Check those rows again in `py annotate.py`, *Translation table* (it shows both definitions), then run again. |
| *N row(s) of name_mapping.csv still need checking* | Rows added by an earlier run aren't checked yet. | Check them in `py annotate.py`, *Translation table* (or in the CSV: fix `name_in_gtt` and `swap_subject_and_object` where wrong, then set `checked` to `yes`), then run again. |
| *N checked row(s) … name something that isn't one of your names* | A typo in `name_in_gtt`. | Use one of your names, or `(none)`. |
| *name_mapping.csv lacks the column(s) …* | The file's header was changed. | Restore the header: `kind,name_from_past_or_crt_schema,name_in_gtt,swap_subject_and_object,checked,definition_from_past_or_crt_schema`. |
| *kind must be 'entity class' or 'predicate'* | A typo in `kind`. | Fix it. |
| *Nothing to score yet* | No finished ground truth record that 060 extracted is in the fair part. | Finish records in `py annotate.py`, then run 060. |
| *splits.json has no tuning / held-out part* | An old `splits.json`. | Delete 030's `splits.json`, run `py 030_split.py`. |
| *missing input files … run 060_extract first* | 060 hasn't run. | Run it. |
| *model must name a model* | The `model` setting is empty. | Give a model's name (`py models.py` lists them). |
| *Test call to … failed* | Ask Sage refuses you that model, the key is wrong, or Ask Sage can't be reached. Nothing else was called. | If Ask Sage says the model isn't allowed, choose another (`--model`; `py models.py` lists them). Otherwise check `.env` and the network. |
| *Cancelled. Nothing was spent.* | You declined at the confirmation. | — |

## Audit trail

- **Log.** `outputs/logs/<run id>.log` records the command line, the settings, the git commit, the model call's retries (if any), each move's duration, each output file's hash and, on failure, the full traceback.
- **Origin.** Each row of `matches.csv` has an `origin` column naming the 060 row it compares (`060_extract/extracted_triples.csv#<position>`) and the ground truth row (`annotations/ground_truth/batch_000.csv#<position>`); the ground truth is made by a person, so a trace stops there.
- **Trace.** `py audit.py <record id>` follows a record back through every step's output to the 010 batch file and the API request that first returned it (`instructions/000_audit.md`).
- **Held-out looks.** `annotations/held_out_looks.csv` keeps one line per look at the held-out part, in Git.

## Human work

- **Check the translation table** (`annotations/name_mapping.csv`) whenever 070 adds rows: `py annotate.py`, button *Translation table*, shows each row with both definitions and an example triple. A wrong translation silently turns right facts into wrong ones, or the reverse.
- **After adding names to your schema**, look at the report's *The translation table*: rows that say `(none)` beside your names that nothing translates to. A row checked as `(none)` before you added a matching name of yours stays `(none)` until you fix it (070 never changes a row).
- **Read `per_record.md`**, especially the partial matches (could be fooled) and the "extracted but not in the ground truth" facts: some may be real facts you missed while annotating, which means the ground truth undercounts.
- **Look at the held-out part only at the end**, and commit `annotations/held_out_looks.csv` after each look.
- **Add schema names only from the tuning part** (or outside knowledge): adding names because of what the held-out records need is tuning on them.

## Known limits

- **Not yet run with the real model.** As of 2026-09-29, 070 has been tested only with a hand-made 060 output whose right answers were worked out in advance (all 16 numbers matched), and with synthetic records for the margins; 060 itself hasn't run with the real model yet, because Ask Sage can't be reached from the laptop it was built on. The numbers in this guide come from those tests, not from a real run.
- **One translation per name.** A name of 060's schema translates to one of yours at most; if it covers two of yours (e.g. `Instrument` for your `Instrument` and `Sensor`), pick the closer one.
- **Partial matching can be fooled**, and doesn't catch synonyms ("the satellite" for "Aqua"). Every partial pair is listed so you can see it.
- **The ground truth started as a model's draft**: recall may be overstated (see Purpose).
- **The threshold of 20 records** for a margin is a rule of thumb.
