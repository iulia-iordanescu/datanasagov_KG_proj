# Review page

A page for subject-matter experts (colleagues new to this project) to read the [ground truth schema](../docs/terminology.md#3-schemas) and the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070), and to comment on them, without installing anything and without being able to change either file.

```
py helpers/review_page.py                     writes the page: outputs/review/review_<date>_<commit>.html
py helpers/review_page.py --read              reads the comment files in annotations/reviews/
py helpers/review_page.py --read <folder or files ...>
```

Free: no [model calls](../docs/terminology.md#8-the-pipeline), no network.

## Making the page

`py helpers/review_page.py` reads `annotations/ground_truth_schema.txt` and `annotations/component_class_mapping.csv` with the same code the [steps](../docs/terminology.md#8-the-pipeline) use (`common/common_helpers/schema_io.py`, `common/common_helpers/component_class_mapping.py`) and writes one HTML file to `outputs/review/`, named by the day and the Git commit, e.g. `review_2026-10-24_8ca4ff5.html`. If either file has changes not yet committed, the name ends with `_edited-` and a short [fingerprint](../docs/terminology.md#8-the-pipeline) of the two files, so two different copies never share a name. `outputs/` isn't in Git, so only I make the page, from my copy of the repository; I send the file itself.

Everything is inside that one file: the styles, the typefaces, the script and the data. It opens by double-click in Chrome, Edge or Firefox, from wherever it was saved, and it loads nothing from the network (its Content-Security-Policy forbids any request). It looks like the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples): its style sheets are copied from `helpers/annotator/page.html` each time the page is made, and its typefaces from `helpers/annotator/fonts/`, so a change to the tool's look reaches the page the next time it is made.

## What the page shows

- **The line under the title bar**: that it is a read-only copy that can't change anything, when it was made, the Git commit, the page version (the file's name), and each file's fingerprint (SHA-256, first 12 characters).
- **How to read this**: what the two files are and what to look for, in plain words, with the reviewer's name field, a box for general comments, and the buttons to save and load comments.
- **Ground truth schema**: the [entity classes](../docs/terminology.md#3-schemas) and predicates, in the file's order, each with its definition; under a predicate, its [patterns](../docs/terminology.md#3-schemas) as the file lists them (the ground truth itself may use more) and its `only:` line, if it is a [pinned predicate](../docs/terminology.md#3-schemas); the `source:` line of each entry that has one; and the file's lines of explanation, under *Notes in the file*. Tabs for entity classes and predicates, a search box, and filters (only pinned predicates; only those commented on; only those changed since the reviewer last looked).
- **Translation table**: one box per [row](../docs/terminology.md#8-the-pipeline), as in the annotation tool: the [component class](../docs/terminology.md#3-schemas) of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) (or a past schema) → the one of the ground truth schema it translates to, both definitions as the row stores them, a made-up example for a predicate (`A CARRIES B → B ABOARD A`), and whether the row is checked. A ⚑ marks a row whose ground truth schema definition changed since it was checked (stale, see [row state](../docs/terminology.md#7-evaluating-extraction-step-070)). The same tabs, search and filters, plus the annotation tool's choice of rows by what they translate to.
- **Terms**: the terms the page uses, copied from `docs/terminology.md` when the page is made (the list is `GLOSSARY` in `helpers/review_page.py`; a term missing from terminology.md stops the page from being made, so no definition is ever written twice).

Both lists can be shown all at once or one at a time (the ↑ and ↓ keys go through them).

## How comments come back

1. A reviewer types in the box under any entry or row, or in *General comments*, and their name. Each comment is kept in their browser as they type (localStorage, on their computer only), so they can stop and come back; the top of the page counts the comments written. If the browser doesn't let the page keep them (some private windows), the page says so, and they must download before closing.
2. **Download my comments** saves a small CSV file (UTF-8), `comments_<name>_<date>.csv`, one row per comment, with the columns `reviewer`, `page_version`, `git_commit`, `kind` (`general`, `entity class`, `predicate`, or `translation row`), `entry` (the component class, or for a row its kind and the current schema's component class, e.g. `predicate CARRIES`; `(general)` for a general comment), `entry_text_shown` (the entry as the page showed it when the comment was written, so the comment still makes sense after the entry changes), `comment`, and `timestamp`. They email it to me.
3. I put each file I receive in `annotations/reviews/` as it is, and commit it: the files are small, made by people, and can't be rebuilt, like the rest of `annotations/`, and they record why a schema entry changed. The page tells reviewers that their name and comments are kept with the project's files. Nothing goes into that folder but files reviewers sent.
4. `py helpers/review_page.py --read` reads every CSV file there (or the files and folders named) and writes a summary to `outputs/review/comments_<date>_<time>.md`, also printed: grouped into general comments, entity classes, predicates and rows of the translation table, then by entry, each comment with its reviewer, date and page version. A comment whose entry has changed since the page it was written on is flagged ⚑, with the entry then and now; one whose entry is no longer in the files is flagged too. One reviewer's comment on one entry counts once, the latest: a reviewer who downloads twice sends the same comments twice. A file without the page's columns is skipped, and the summary says so.

## Sending a newer copy

Comments are filed by entry (its kind and component class), not by page, so they carry over: a reviewer who opens a newer copy in the same browser finds their comments under the same entries, and a comment written when the entry read differently says so under its box. The page also remembers the entries of the copies a reviewer opened before (up to three), and marks each entry that changed since the copy opened before it (⚑ *changed since you last looked*, the old text on hover) or is new. Comments on entries the newer copy no longer has are listed under *How to read this*, and stay in the download. In another browser or on another computer, **Load my comments from a file** reads a downloaded comment file back in.

## What it can't do

- It can't change anything: no server, no network, no file written except the reviewer's own download. A reviewer's suggestions reach the files only through me.
- It shows the ground truth schema's patterns as its file lists them, not the patterns the ground truth itself uses (the annotation tool's **Help → Ground truth schema** shows those).
- It doesn't know which rows of the translation table the current schema still uses: it shows every row, with the definitions the row stores.
- Comments kept in a browser are lost if the reviewer clears its site data before downloading.
