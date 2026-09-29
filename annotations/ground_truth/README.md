# Ground truth

This folder **is** the ground truth: every `batch_*.csv` file in it, taken together. Each file is one batch of records a person has checked and corrected. Steps read the folder; no step ever writes into it.

| File | What it holds |
|---|---|
| `batch_000.csv` | The records annotated before the pipeline existed (pool positions 0–5, 2026-09). |
| `batch_001.csv`, `batch_002.csv`, … | Each one corrected from step 050's draft batch of the same number. |

## Adding a batch: use the annotation tool

After running step 050, from the repository folder:

```
py annotate.py
```

It opens a page in your browser (Ctrl+C in the terminal stops it). It runs only on your computer: no internet, no model calls, nothing to install.

1. **Pick the batch** at the top of the page. The first time you open a draft batch, the tool copies it here, renamed by its batch number (`outputs/intermediate_results/050_annotate/drafted_triples_batch1.csv` → `annotations/ground_truth/batch_001.csv`). From then on you're editing that copy; the draft in `outputs/` is never changed.
2. **Correct each record**: read its text first (the source text of each row is highlighted in it; the row you're on is darker), then fix, delete (🗑) or add (+) rows. Entity classes and predicates suggest the hand-built schema's names as you type; you can still type a new one. To set a source text, select the passage in the text and press **Use selection**. Every change is saved to the file at once, and the checks under each row update as you go (✖ must be fixed, ⚑ worth a look).
3. **Tick "All facts extracted"** on a record once every fact its text states is there. That sets `all_facts_extracted` to `1` on all its rows; untick it for a record you haven't finished.
4. **Commit** the file to Git, so the work is safe.

The tool also opens the files already here, like `batch_000.csv`. The first time it saves a file, it rewrites it in its own plain format: the same rows and values, but the CSV quoting may change, so Git can show more lines changed than you edited. Deleting every row of a record keeps one row holding only its id, which means "annotated, states no facts". The draft's `flags` column isn't kept, since the tool recomputes the checks.

**Without the tool**, the same result by hand: copy the draft batch here under its new name, correct it in any editor (the `flags` column can stay; it's ignored), set `all_facts_extracted` to `1` on every row of each finished record, and commit. Never correct the file in `outputs/`: it can be deleted and rebuilt, and your corrections would go with it.

## The columns

`id, subject, subject_class, predicate, object, object_class, source_text, all_facts_extracted` (a draft's `flags` column may stay). One row per triple instance, grouped by record. A row with an `id` but an empty subject, predicate and object says "this record was annotated and states no facts". Terms: [docs/terminology.md](../../docs/terminology.md).

## What the pipeline checks

Every step that reads this folder (`common/ground_truth.py`) reports, and never silently fixes:

- a record in two files (annotated twice): keep it in one file;
- a record whose rows disagree on `all_facts_extracted`: set it the same on every row;
- a file missing one of the columns above.
