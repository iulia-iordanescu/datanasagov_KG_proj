# Annotations

Work made by a person, kept in Git because it can't be rebuilt by rerunning the pipeline. Steps read these files; no step writes here, with two narrow exceptions: step 070 may add lines at the end of `component_class_mapping.csv` and `held_out_looks.csv`, never changing or deleting a line already there. Terms: [docs/terminology.md](../docs/terminology.md).

| File or folder | What it holds | Read by |
|---|---|---|
| `ground_truth/` | The ground truth: one file per corrected batch, written with the annotation tool (`py helpers/annotate.py`). How to add a batch: below. | 050 (to skip records already done, and to check the files for typos), 060 (which records are finished), 070 (the answer key) |
| `ground_truth_candidates.csv` | The ground truth candidates pool: 1,000 records drawn once (2026-09-21), in their shuffled order, each with its maintainer and the sampling group it was drawn from (`group`, `group_size`, `drawn_from_group`). | 030, 070 (the groups) |
| `ground_truth_candidates.json` | How the pool was drawn: stratified by maintainer, seed 1000, 1,000 of 36,323 records, and each group's size and places. | nothing (a record of the draw) |
| `schema_derived_from_manual_annotation.txt` | The hand-built schema: entity classes and predicates with a description each, and the patterns each predicate has been used in. It grows as annotation goes: add each component class you coin while annotating, with a one-line definition, and each new pattern, with the annotation tool's buttons (or by hand). The tool gives each component class it adds a `source:` line naming the ground truth records that use it, by part. Step 050's report also lists the component classes still missing. | 040 (to compare with), 050 (shown to the model; every row is checked against it), the annotation tool; 060 with `--schema`; 070 (the ground truth vocabulary) |
| `schema_additions.txt` | Entity classes and predicates to add to the schema step 060 extracts with (e.g. a mentor's suggestions), each with a `source:` line saying where the idea came from; a component class learned from the ground truth must come from tuning records, named by pool position (`source: ground truth tuning #12`), or 060 leaves it out. Easiest edited in the annotation tool (*Schema additions*), which keeps the layout right. Starts empty. Its layout: [060_extract/060_extract.md](../060_extract/060_extract.md). | 060 |
| `component_class_mapping.csv` | The translation of the component classes of the schema 060 used into the ground truth vocabulary: one row per component class (`kind`, `component_class_from_past_or_crt_schema`, `component_class_in_gtt`, `swap_subject_and_object`, `checked`, `definition_from_past_or_crt_schema`). 070 adds rows for new component classes (proposed by the model, `checked` = `no`); you check them. How: [070_evaluate/070_evaluate.md](../070_evaluate/070_evaluate.md). | 070 |
| `partial_pair_reviews.csv` | Your verdicts on step 070's partial pairs (`same fact` / `not the same fact`), tuning records only, made with the annotation tool (*Partial pairs*). 070 never pairs two triples you marked `not the same fact`. Starts with its header only. | 070 |
| `held_out_looks.csv` | One line per time the held-out part's numbers were looked at (`date`, `run_id`, `schema`, `held_out_records`: how many held-out records were evaluated). 070 adds a line with `--evaluate_held_out true`; commit it. | 070 |
| `schema_notes_derived_from_manual_annotation.txt` | The notes the hand-built schema started from. Kept as a record only. | nothing |
| `archive/` | The five draft batches made before the pipeline existed (`draft_triples_batch1–5`, each a CSV and its settings), drafts of 3 of the 6 records in `ground_truth/batch_000.csv`. Kept as a record only. | nothing |

## Annotating ground truth: the annotation tool

After running step 050, from the repository folder:

```
py helpers/annotate.py
```

It opens a page in your browser (Ctrl+C in the terminal stops it). On any view, **Help** at the top shows this file's section about that view. It runs only on your computer: no internet, no model calls, nothing to install.

1. **Pick the batch** at the top of the page. The first time you open a draft batch, the tool copies it into `ground_truth/`, renamed by its batch number (`outputs/intermediate_results/050_annotate/drafted_triples_batch1.csv` → `annotations/ground_truth/batch_001.csv`). From then on you're editing that copy; the draft in `outputs/` is never changed.
2. **Correct each record**: its heading shows its pool position and whether it's a **tuning** or **held-out** record (a component class you learn from a held-out record must not go into `schema_additions.txt`). Read its text first (the source text of each row is highlighted in it; the row you're on is darker), then fix, delete (🗑) or add (+) rows. Entity classes and predicates suggest the component classes of the ground truth vocabulary as you type (the hand-built schema's, plus any already coined in the ground truth); you can still type a new one. An entity class or predicate not in the hand-built schema stays flagged (it could be a typo). If it's a typo, fix it; if it's new, press **Add … to the hand-built schema** under the flag, type a one-line definition and press **Add**. A pattern the hand-built schema doesn't have yet (a predicate between two entity classes it hasn't joined before) is flagged the same way, with an **Add the pattern** button once its subject class and object class are in the schema. The bar above the page lists, from every batch, the component classes the ground truth uses that the hand-built schema lacks, and the patterns it lacks whose component classes are all in it, with the same buttons. The tool adds only that entry or pattern to `schema_derived_from_manual_annotation.txt`, checks nothing else in it changed (otherwise it puts the file back and says so), and gives each component class a `source:` line naming the ground truth records that use it, by part (`source: ground truth tuning #3; held-out #8`). A pattern gets no `source:` line: the layout has none for patterns. To set a source text, select the passage in the text and press **Use selection**. Every change is saved to the file at once, and the checks under each row update as you go (✖ must be fixed, ⚑ worth a look).
3. **Tick "All facts extracted"** on a record once every fact its text states is there. That sets `all_facts_extracted` to `1` on all its rows; untick it for a record you haven't finished.
4. **Commit** the file to Git, so the work is safe.

The tool also opens the files already in `ground_truth/`, like `batch_000.csv`. The first time it saves a file, it rewrites it in its own plain format: the same rows and values, but the CSV quoting may change, so Git can show more lines changed than you edited. Deleting every row of a record keeps one row holding only its id, which means "annotated, states no facts". The draft's `flags` column isn't kept, since the tool recomputes the checks.

**Without the tool**, the same result by hand: copy the draft batch into `ground_truth/` under its new name, correct it in any editor (the `flags` column can stay; it's ignored), set `all_facts_extracted` to `1` on every row of each finished record, and commit. Never correct the file in `outputs/`: it can be deleted and rebuilt, and your corrections would go with it.

### Checking the translation table

Press **Translation table** at the top of the page. It shows `component_class_mapping.csv` one row per component class of the current schema (the one step 060 used last), and opens on the rows still to check (untick *Show only rows to check* to see them all). Rows only past schemas use are hidden (tick *Show the … row(s) only past schemas use* to see them): they are kept so that a component class that comes back in a later schema needn't be checked again. Each row shows:

- the component class and its definition in the current schema;
- **Means, in the ground truth vocabulary**: a list of the ground truth vocabulary's component classes (and `(none)`), with the chosen one's definition below it;
- for a predicate, **Swap subject and object**, with an example: the first triple extraction kept with that predicate, before and after translation (`Aqua CARRIES MODIS --> MODIS ABOARD Aqua`), so you can read whether it says the same thing;
- **⚑ suggested**: a row that says `(none)`, for which the model, at evaluation's last run, suggested a ground truth component class gained since (a different spelling, e.g. `Gadget` --> `Device`). Pick it if right.
- **⚑ now exists**: a row that says `(none)`, though the ground truth vocabulary now has a component class spelled the same (you coined it since, or added it to the hand-built schema). Probably out of date: change it, unless the ground truth's component class means something else.
- **⚑ shared**: if another component class of the current schema already translates to the one you chose, the row says so: evaluation won't be able to tell those component classes apart. Fine if your ground truth doesn't make that distinction.
- **Checked**: tick it once the translation is right; that also stores the current schema's definition of the component class in the row. A row whose two component classes are the same says so and needs nothing.
- **⚑ stale**: a row checked when the current schema's component class had another definition. It shows that old definition, counts as unchecked, and needs ticking again once you've confirmed (or fixed) the translation.

Every change is saved to `component_class_mapping.csv` at once. The tool can't add or reorder rows (step 070 adds them), and the only rows it can delete are repeats: one component class, one row, so if a hand edit left two rows for the same component class, the page says so and shows a **Delete this row** button on each (keep the right one, usually the one whose stored definition matches the current schema's). If step 070 adds rows while the page is open, a save keeps them; if the rows on the page no longer match the file, the save is refused and the page asks you to reload.

### Reviewing partial pairs

Press **Partial pairs** at the top of the page, after a run of step 070. A partial pair is a ground truth triple and an extracted triple whose predicates agree but whose subjects or objects agree only loosely: one contained in the other as whole words, either way round (`MODIS` and `Moderate Resolution Imaging Spectroradiometer (MODIS)`, but also `MODIS` and `MODIS Terra`, a different satellite). Each card shows both triples (the extracted one translated into the ground truth vocabulary) and, unfolded, the record's text. Press **Same fact** or **Not the same fact**; **Take back** removes a verdict. Every verdict is saved to `partial_pair_reviews.csv` at once; rerun step 070 to see its effect. Only tuning records are shown: reviewing held-out pairs would mean looking at held-out results.

### Adding to the schema additions

Press **Schema additions** at the top of the page. It lists the entries of `schema_additions.txt` (*Edit*, *Delete*) and opens a form with **+ Add an entry**: kind, component class (one word: entity classes in CamelCase, predicates in UPPER_SNAKE_CASE), a one-line definition, patterns for a predicate (`Subject -> Object; …`) and the source. What's wrong is shown as you type, and the tool won't save an entry that is wrong: no definition, no source, or a source naming the ground truth that doesn't say `tuning` or names a held-out record (`source: ground truth tuning #12, #15`; the same check step 060 makes). The comments at the top of the file are kept.

Two shortcuts:

- **On a tuning record's page:** *Add a component class to the schema additions* opens the form with `source: ground truth tuning #<its position>` filled in. On a held-out record the button is greyed out.
- **Component classes outside the schema:** below the entries, the component classes extraction's last run used that the current schema doesn't have (held-out records never counted), each with *Add*, which fills in the kind, component class and source. You write the definition.

## The ground truth files

The ground truth is every `batch_*.csv` file in `ground_truth/`, taken together. `batch_000.csv` holds the records annotated before the pipeline existed (pool positions 0–5, 2026-09); `batch_001.csv`, `batch_002.csv`, … are each corrected from step 050's draft batch of the same number.

Their columns:

`id, subject, subject_class, predicate, object, object_class, source_text, all_facts_extracted` (a draft's `flags` column may stay). One row per triple instance, grouped by record. A row with an `id` but an empty subject, predicate and object says "this record was annotated and states no facts".

### What the pipeline checks

Every step that reads `ground_truth/` (050, 060 and 070, through `common/common_helpers/ground_truth.py`) lists these in its report's warnings, and the annotation tool shows them on its page; none is ever silently fixed:

- a record in two files (annotated twice): keep it in one file;
- the same triple twice in one record: delete one of the two rows;
- a record whose rows disagree on `all_facts_extracted`: set it the same on every row;
- a file missing one of the columns above.
