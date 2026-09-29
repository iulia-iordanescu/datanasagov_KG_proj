# Annotations

Work made by a person, kept in Git because it can't be rebuilt by rerunning the pipeline. Steps read these files; no step ever writes here. Terms: [docs/terminology.md](../docs/terminology.md).

| File or folder | What it holds | Read by |
|---|---|---|
| `ground_truth/` | The ground truth: one file per corrected batch, written with the annotation tool (`py annotate.py`). How to add a batch: [ground_truth/README.md](ground_truth/README.md). | 050 (to skip records already done, and to check the files for typos), 060 (which records are finished), 070 (to score against it) |
| `ground_truth_candidates.csv` | The ground truth candidates pool: 1,000 records drawn once (2026-09-21), in their shuffled order, each with its maintainer and the sampling group it was drawn from (`group`, `group_size`, `drawn_from_group`). | 030 |
| `ground_truth_candidates.json` | How the pool was drawn: stratified by maintainer, seed 1000, 1,000 of 36,323 records, and each group's size and places. | nothing (a record of the draw) |
| `schema_derived_from_manual_annotation.txt` | The hand-built schema: entity classes and predicates with a description each, and the patterns each predicate has been used in. Updated by hand as annotation goes. | 040 (to compare with), 050 (shown to the model; every row is checked against it), the annotation tool; 060 with `--schema` |
| `schema_additions.txt` | Entity classes and predicates to add to the schema step 060 extracts with (e.g. a mentor's suggestions), each with a `source:` line saying where the idea came from. Starts empty. Its layout: [instructions/060_extract.md](../instructions/060_extract.md). | 060 |
| `schema_notes_derived_from_manual_annotation.txt` | The notes the hand-built schema started from. Kept as a record only. | nothing |
| `archive/` | The five draft batches made before the pipeline existed (`draft_triples_batch1–5`, each a CSV and its settings), drafts of 3 of the 6 records in `ground_truth/batch_000.csv`. Kept as a record only. | nothing |
