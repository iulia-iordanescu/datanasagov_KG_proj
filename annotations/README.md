# Annotations

Work made by a person, kept in Git because it can't be rebuilt by rerunning the pipeline. Steps read these files; no step writes here, with two narrow exceptions: step 070 may add lines at the end of `name_mapping.csv` and `held_out_looks.csv`, never changing or deleting a line already there. Terms: [docs/terminology.md](../docs/terminology.md).

| File or folder | What it holds | Read by |
|---|---|---|
| `ground_truth/` | The ground truth: one file per corrected batch, written with the annotation tool (`py annotate.py`). How to add a batch: below. | 050 (to skip records already done, and to check the files for typos), 060 (which records are finished), 070 (the answer key) |
| `ground_truth_candidates.csv` | The ground truth candidates pool: 1,000 records drawn once (2026-09-21), in their shuffled order, each with its maintainer and the sampling group it was drawn from (`group`, `group_size`, `drawn_from_group`). | 030, 070 (the groups) |
| `ground_truth_candidates.json` | How the pool was drawn: stratified by maintainer, seed 1000, 1,000 of 36,323 records, and each group's size and places. | nothing (a record of the draw) |
| `schema_derived_from_manual_annotation.txt` | The hand-built schema: entity classes and predicates with a description each, and the patterns each predicate has been used in. Updated by hand as annotation goes: add each name you coin while annotating, with a definition (the annotation tool and step 050's report list the ones still missing). | 040 (to compare with), 050 (shown to the model; every row is checked against it), the annotation tool; 060 with `--schema`; 070 (your names) |
| `schema_additions.txt` | Entity classes and predicates to add to the schema step 060 extracts with (e.g. a mentor's suggestions), each with a `source:` line saying where the idea came from; a name learned from the ground truth must come from tuning records, named by pool position (`source: ground truth #12`), or 060 leaves it out. Starts empty. Its layout: [instructions/060_extract.md](../instructions/060_extract.md). | 060 |
| `name_mapping.csv` | The translation of the names of the schema 060 used into yours: one row per name (`kind`, `name_from_past_or_crt_schema`, `name_in_gtt`, `swap_subject_and_object`, `checked`, `definition_from_past_or_crt_schema`). 070 adds rows for new names (proposed by the model, `checked` = `no`); you check them. How: [instructions/070_evaluate.md](../instructions/070_evaluate.md). | 070 |
| `held_out_looks.csv` | One line per time the held-out part's numbers were looked at (`date`, `run_id`, `schema`, `held_out_records`: how many held-out records were scored). 070 adds a line with `--score_held_out true`; commit it. | 070 |
| `schema_notes_derived_from_manual_annotation.txt` | The notes the hand-built schema started from. Kept as a record only. | nothing |
| `archive/` | The five draft batches made before the pipeline existed (`draft_triples_batch1–5`, each a CSV and its settings), drafts of 3 of the 6 records in `ground_truth/batch_000.csv`. Kept as a record only. | nothing |

## Annotating ground truth: the annotation tool

After running step 050, from the repository folder:

```
py annotate.py
```

It opens a page in your browser (Ctrl+C in the terminal stops it). It runs only on your computer: no internet, no model calls, nothing to install.

1. **Pick the batch** at the top of the page. The first time you open a draft batch, the tool copies it into `ground_truth/`, renamed by its batch number (`outputs/intermediate_results/050_annotate/drafted_triples_batch1.csv` → `annotations/ground_truth/batch_001.csv`). From then on you're editing that copy; the draft in `outputs/` is never changed.
2. **Correct each record**: its heading shows its pool position and whether it's a **tuning** or **held-out** record (a name you learn from a held-out record must not go into `schema_additions.txt`). Read its text first (the source text of each row is highlighted in it; the row you're on is darker), then fix, delete (🗑) or add (+) rows. Entity classes and predicates suggest the names of the ground truth vocabulary as you type (the hand-built schema's, plus any already coined in the ground truth); you can still type a new one. A name not in the hand-built schema stays flagged (it could be a typo), and the page lists every such name above the batches, so you can add it, with a definition, to the hand-built schema. To set a source text, select the passage in the text and press **Use selection**. Every change is saved to the file at once, and the checks under each row update as you go (✖ must be fixed, ⚑ worth a look).
3. **Tick "All facts extracted"** on a record once every fact its text states is there. That sets `all_facts_extracted` to `1` on all its rows; untick it for a record you haven't finished.
4. **Commit** the file to Git, so the work is safe.

The tool also opens the files already in `ground_truth/`, like `batch_000.csv`. The first time it saves a file, it rewrites it in its own plain format: the same rows and values, but the CSV quoting may change, so Git can show more lines changed than you edited. Deleting every row of a record keeps one row holding only its id, which means "annotated, states no facts". The draft's `flags` column isn't kept, since the tool recomputes the checks.

### Checking the translation table

Press **Translation table** at the top of the page. It shows `name_mapping.csv` one row per name of the current schema (the one step 060 used), and opens on the rows still to check (untick *Show only rows to check* to see them all). Each row shows:

- the name and its definition in the current schema;
- **Means, in the ground truth vocabulary**: a list of the ground truth vocabulary's names (and `(none)`), with the chosen name's definition below it;
- for a predicate, **Swap subject and object**, with an example: the first triple extraction kept with that predicate, before and after translation (`Aqua CARRIES MODIS → MODIS ABOARD Aqua`), so you can read whether it says the same thing;
- **Checked**: tick it once the translation is right; that also stores the current schema's definition of the name in the row. A row whose two names are the same says so and needs nothing.
- **⚑ stale**: a row checked when the current schema's name had another definition. It shows that old definition, counts as unchecked, and needs ticking again once you've confirmed (or fixed) the translation.

Every change is saved to `name_mapping.csv` at once. The tool can't add, remove or reorder rows (step 070 adds them). If step 070 adds rows while the page is open, a save keeps them; if the rows on the page no longer match the file, the save is refused and the page asks you to reload.

**Without the tool**, the same result by hand: copy the draft batch into `ground_truth/` under its new name, correct it in any editor (the `flags` column can stay; it's ignored), set `all_facts_extracted` to `1` on every row of each finished record, and commit. Never correct the file in `outputs/`: it can be deleted and rebuilt, and your corrections would go with it.

## The ground truth files

The ground truth is every `batch_*.csv` file in `ground_truth/`, taken together. `batch_000.csv` holds the records annotated before the pipeline existed (pool positions 0–5, 2026-09); `batch_001.csv`, `batch_002.csv`, … are each corrected from step 050's draft batch of the same number.

Their columns:

`id, subject, subject_class, predicate, object, object_class, source_text, all_facts_extracted` (a draft's `flags` column may stay). One row per triple instance, grouped by record. A row with an `id` but an empty subject, predicate and object says "this record was annotated and states no facts".

### What the pipeline checks

Every step that reads `ground_truth/` (050, 060 and 070, through `common/ground_truth.py`) lists these in its report's warnings, and the annotation tool shows them on its page; none is ever silently fixed:

- a record in two files (annotated twice): keep it in one file;
- a record whose rows disagree on `all_facts_extracted`: set it the same on every row;
- a file missing one of the columns above.
