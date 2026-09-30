# 070_evaluate

Terms (precision, recall, match, margin of error, bootstrap, tuning part, held-out part, …) are as defined in [docs/terminology.md](../docs/terminology.md), section *Scoring extraction*.

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
| `extracted` | `060_extract/extracted_triples.csv` | What 060 kept. |
| `extraction_details` | `060_extract/extraction_details.json` | Which records 060 extracted (a record whose call failed is not scored, not scored as zero). |
| `schema_used` | `060_extract/schema_used.json` | The schema 060 used: the names to translate. |
| `splits` | `030_split/splits.json` | The pool's order, and each record's part (tuning or held-out). |
| `records` | `020_clean/records.jsonl` | Titles, for the per-record list. |
| `ground_truth` | `./annotations/ground_truth/batch_*.csv` (in Git) | The answer key. Only records you've finished (*All facts extracted*) are scored. |
| `candidates` | `./annotations/ground_truth_candidates.csv` (in Git) | Each pool record's sampling group. |
| `hand_schema` | `./annotations/schema_derived_from_manual_annotation.txt` (in Git) | Your names, with their definitions. Your names also include any used in the ground truth. |
| `name_mapping` | `./annotations/name_mapping.csv` (in Git) | The translation table (below). |

## Outputs

In `outputs/intermediate_results/070_evaluate/`, rewritten by each run:

| File | For | What's in it |
|---|---|---|
| `per_record.md` | you, reading | Each scored record: what it describes (✓/✗), its facts **matched** (✓ exact or ≈ partial, with the ground truth's version when they differ), **extracted but not in the ground truth** (they count against precision) and **in the ground truth but not extracted** (against recall; marked *out of reach* when the schema can't express them). Extracted facts are shown translated into your names. Opens well in VS Code or on GitHub. |
| `matches.csv` | you, sorting and filtering (e.g. in Excel) | One row per fact: record, pool position, part, group, `status` (`exact`, `partial`, `wrong`, `missed`), `entity_classes_right`, `within_reach`, then the fact as extracted, as translated, and as in the ground truth, and where each came from (`origin`). |
| `scores.json` | the computer, to compare runs | Every number (each with `value`, `low`, `high`: the margin), per part and per sampling group; which records were scored and which left out, and why; the settings. |
| `cache/` | | The model's proposed translations, so a rerun doesn't pay again. |
| `_manifest.json` | | Run id, settings, input files and their hashes, output hashes, headline numbers. |

The report (`outputs/reports/<run id>.md`) shows the numbers, the group table and every warning; read it first.

**Two files in `annotations/` that 070 adds to**, the only exceptions to "no step writes into `annotations/`". 070 only ever **adds** lines at their end; a line already there is never changed or deleted:

| File | What 070 adds |
|---|---|
| `annotations/name_mapping.csv` | Rows for names of 060's schema that have none yet (see *Translating names*). |
| `annotations/held_out_looks.csv` | One line per run with `--score_held_out true`: date, run id, schema used, held-out records scored. Commit it: it's how the looks are counted, across laptops and after `outputs/` is deleted. |

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `score_held_out` | false | Also show the held-out part's numbers, and log the look in `annotations/held_out_looks.csv`. | Only at the end, for the numbers you report. Each look is a chance to tune on the held-out part without meaning to. |
| `confirm_paid_calls` | true | Stop and ask before a model call. 070 calls the model only to propose translations for names it has no row for. | `false` for runs with nobody at the keyboard. |

The numbers that are fixed on purpose (in `070_evaluate/stats.py`): `MIN_RECORDS = 20` (fewer scored records: no margin), `RESHUFFLES = 1000`, `SEED = 70` (a rerun gives the same margins), `SHARE_GAP = 0.10` (see Checks).

## How to run

```
py 070_evaluate.py                           the tuning part
py 070_evaluate.py --score_held_out true     also the held-out part (for the end; each look is logged)
```

Needs 060's output. The first run with a new schema stops after adding rows to `annotations/name_mapping.csv`: check them, then run again.

## How it works

1. **Choose the records** (`records.py`). A record is scored if you've finished it in the ground truth and 060's last run extracted it. Of those, only the **fair part**: the longest run of the pool's first records that are all scored. A record after a gap (an unfinished or unextracted pool record before it) or outside the pool is left out and named, so every scored record belongs to a fair sample.
2. **Translate names** (`names.py`), through `annotations/name_mapping.csv`:

   ```
   kind,induced_name,your_name,reversed,checked
   entity class,Satellite,Spacecraft,no,yes
   predicate,CARRIES,ABOARD,yes,yes          "A CARRIES B" is "B ABOARD A"
   entity class,Gadget,(none),no,yes         nothing of yours means this
   entity class,Dataset,Dataset,no,same name
   ```

   For each name of 060's schema without a row: one equal to one of yours (ignoring case, spaces and punctuation) gets a row at once, `checked` = `same name`; the model proposes the others (one paid call, after the usual confirmation), `checked` = `no`. The step then stops. You check each `no` row: fix `your_name` (one of your names, or `(none)`) and `reversed` where wrong, then set `checked` to `yes`. Scoring runs only once every row it needs is checked. The model's proposals are only a first draft: in testing, a stand-in's deliberate mistake (`Phase` → `(none)` instead of `MissionPhase`) is exactly what the check is for.
3. **Compare, record by record** (`match.py`). Each extracted fact is translated into your names; a reversed predicate also swaps subject and object. Facts are then paired one to one, in two passes:
   - **exact**: subject and object the same once evened out (case, spacing, quote marks, dashes, edge punctuation and a leading "the/a/an" ignored, as everywhere in the pipeline), predicate the same;
   - **partial**, among the facts still unpaired: the same, except that a subject or object may be contained in the other as whole words: "MODIS" in "Moderate Resolution Imaging Spectroradiometer (MODIS)". This can be fooled ("MODIS" in "MODIS Terra"), which is why every partial pair is listed in `per_record.md`.

   A pair is **strict** when both entity classes also agree. A ground truth fact is **within reach** when its predicate and both its entity classes are names some checked row translates to. The DESCRIBES rows are compared only on their entity class, apart from the facts, since code writes the rest of them.
4. **Score** (`stats.py`). Every number is summed over the records before dividing (a fact is an answer, whichever record it's in):

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

The code: `070_evaluate/` holds `moves.py` (the moves, and writing the results), `records.py`, `names.py`, `match.py`, `stats.py` and `prompts/map_names.txt`. Shared: `common/ground_truth.py` (reading the ground truth; the fair part), `common/text_match.py`, `common/triples_io.py`, `common/files.py` (adding lines without changing any), `common/cache.py`.

## Checks and warnings

Shown **before paying** (when the model is asked for translations), and in the report:

| Message | Meaning | What to do |
|---|---|---|
| *N finished ground truth record(s) weren't extracted by 060's last run* | They can't be scored. | Run `py 060_extract.py`. |
| *N record(s) are left out because they aren't in the fair part* | A pool record before them isn't finished or extracted, or they're outside the pool. | Finish (or extract) the records before them. |
| *N scored record(s) have no sampling group* | Not in the pool file. | Normally impossible for pool records. |

The step **stops** (having scored nothing) with:

| Message | Meaning | What to do |
|---|---|---|
| *Added N row(s) to name_mapping.csv …* | New names of 060's schema. | Check the rows with `checked` = `no`, then run again. |
| *N row(s) of name_mapping.csv still need checking* | | Same. |
| *N checked row(s) … name something that isn't one of your names* | A typo in `your_name`. | Use one of your names, or `(none)`. |
| *kind must be 'entity class' or 'predicate'* | A typo in `kind`. | Fix it. |
| *Nothing to score yet* | No finished ground truth record that 060 extracted is in the fair part. | Finish records in `py annotate.py`, then run 060. |
| *splits.json has no tuning / held-out part* | An old `splits.json`. | Delete 030's `splits.json`, run `py 030_split.py`. |
| *missing input files … run 060_extract first* | 060 hasn't run. | Run it. |

In the report only:

| Message | Meaning |
|---|---|
| *only N record(s) scored, fewer than 20* | No margin of error; don't draw conclusions yet. |
| *some sampling group's share … differs from its share of the pool* | The scored records don't mirror the pool; see the group table. |
| *The held-out part was looked at: N time(s) so far* | After `--score_held_out true`. Commit `annotations/held_out_looks.csv`. |

## Human work

- **Check the translation table** (`annotations/name_mapping.csv`) whenever 070 adds rows. A wrong translation silently turns right facts into wrong ones, or the reverse.
- **Read `per_record.md`**, especially the partial matches (could be fooled) and the "extracted but not in the ground truth" facts: some may be real facts you missed while annotating, which means the ground truth undercounts.
- **Look at the held-out part only at the end**, and commit `annotations/held_out_looks.csv` after each look.
- **Add schema names only from the tuning part** (or outside knowledge): adding names because of what the held-out records need is tuning on them.

## Known limits

- **Not yet run with real data.** As of 2026-09-30, 070 has been tested only with a hand-made 060 output whose right answers were worked out in advance (all 16 numbers matched), and with synthetic records for the margins. 060 itself hasn't run with the real model yet.
- **One translation per name.** A name of 060's schema translates to one of yours at most; if it covers two of yours (e.g. `Instrument` for your `Instrument` and `Sensor`), pick the closer one.
- **Partial matching can be fooled**, and doesn't catch synonyms ("the satellite" for "Aqua"). Every partial pair is listed so you can see it.
- **The ground truth started as a model's draft**: recall may be overstated (see Purpose).
- **The threshold of 20 records** for a margin is a rule of thumb.
