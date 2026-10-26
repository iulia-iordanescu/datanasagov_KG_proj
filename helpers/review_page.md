# Review page

A page for subject-matter experts (colleagues new to this project) to read the [ground truth schema](../docs/terminology.md#3-schemas), the [translation table](../docs/terminology.md#7-evaluating-extraction-step-070), and the questions I would like an expert's answer to, and to comment on them and answer them, without installing anything and without being able to change any file. I send them one link: https://iulia-iordanescu.github.io/datanasagov_KG_proj/review/

```
py helpers/review_page.py                     writes the page: outputs/review/review_<date>_<commit>.html
py helpers/review_page.py --publish           puts the page at the link (the branch gh-pages), and pushes it
py helpers/review_page.py --read              reads the comment files and emails in annotations/reviews/
py helpers/review_page.py --read <folder or files ...>
```

Free: no [model calls](../docs/terminology.md#8-the-pipeline). Only `--publish` uses the network (to push to GitHub).

## Making the page

`py helpers/review_page.py` reads `annotations/ground_truth_schema.txt` and `annotations/component_class_mapping.csv` with the same code the [steps](../docs/terminology.md#8-the-pipeline) use (`common/common_helpers/schema_io.py`, `common/common_helpers/component_class_mapping.py`, through `common/common_helpers/review_comments.py`), and `annotations/questions_for_experts.md` with `common/common_helpers/expert_questions.py` (*The questions file*, below), and writes one HTML file to `outputs/review/`, named by the day and the Git commit, e.g. `review_2026-10-24_8ca4ff5.html`. If one of the three files has changes not yet committed, the name ends with `_edited-` and a short [fingerprint](../docs/terminology.md#8-the-pipeline) of the files, so two different copies never share a name. It refuses to make the page, saying why and where, while a question isn't in the file's format or doesn't agree with its sources. I open it to check it before I publish it.

Everything is inside that one file: the styles, the typefaces, the script and the data. It opens by double-click in Chrome, Edge or Firefox, from wherever it was saved, and it loads nothing from the network (its Content-Security-Policy forbids any request). It looks like the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples): its style sheets are copied from `helpers/annotator/page.html` each time the page is made, and its typefaces from `helpers/annotator/fonts/`, so a change to the tool's look reaches the page the next time it is made.

## The link

`py helpers/review_page.py --publish` makes the page and puts it on the branch `gh-pages` of the repository, as `review/index.html`, beside an empty `.nojekyll` (which tells GitHub Pages to serve the files as they are), then pushes that branch. GitHub Pages serves it at **https://iulia-iordanescu.github.io/datanasagov_KG_proj/review/**, the one link I send.

Why a branch of its own: the branch holds those two files and nothing else, ever. Each publish is one commit whose files are exactly those two, written with Git's own plumbing commands, so my working folder and the branch I'm on are never touched, nothing else of the repository becomes part of the site (not `docs/`, and never `annotations/reviews/`), and `main`'s history doesn't get a 120 KB file each time the page changes. The page shows only the ground truth schema, the translation table, the questions (which quote records of the public catalog) and terms of `docs/terminology.md`, all already public in the repository.

**Once, on GitHub** (after the first `--publish`, which creates the branch): the repository's **Settings → Pages → Build and deployment → Source: Deploy from a branch**, then **Branch: `gh-pages`**, folder **`/ (root)`**, and **Save**. After a minute or two the link works.

**Each update:**

1. Commit the changes to the ground truth schema, the translation table or the questions (and push `main` as usual).
2. `py helpers/review_page.py --publish`. It stops, naming the files, while a file the page is made from has changes not yet committed (the three files, the annotation guidelines and the ground truth the questions are checked against, `docs/terminology.md`, the page's code and look: `PAGE_SOURCES` in `helpers/review_page.py`), because the page says which commit it shows. If the page at the link already shows the same commit and the same files, it publishes nothing and says so.
3. The same link shows the new version a minute or two later (GitHub Pages rebuilds the site on each push). A reviewer who opens it again in the same browser keeps their comments (see *Sending a newer copy*).

## What the page shows

- **The line under the title bar**: one short line, *Read-only · updated* and the day the page was made (and, for a reviewer who opened an older copy before, how many entries changed or are new since). Its **details** opens the full version: that it is a read-only copy that can't change anything, when it was made, the Git commit, the page version (the file's name), and each file's fingerprint (SHA-256, first 12 characters).
- **How to read this**: what the two files and the questions are and what to look for, in plain words, with the reviewer's name field, a box for general comments, and the buttons to send, save and load comments.
- **Ground truth schema**: the [entity classes](../docs/terminology.md#3-schemas) and predicates, in the file's order, each with its definition; under a predicate, its [patterns](../docs/terminology.md#3-schemas) as the file lists them (the ground truth itself may use more) and its `only:` line, if it is a [pinned predicate](../docs/terminology.md#3-schemas); the `source:` line of each entry that has one; and the file's lines of explanation, under *Notes in the file*. Tabs for entity classes and predicates, a search box, and filters (only pinned predicates; only those commented on; only those changed since the reviewer last looked).
- **Translation table**: one box per [row](../docs/terminology.md#8-the-pipeline), as in the annotation tool: the [component class](../docs/terminology.md#3-schemas) of the [current schema](../docs/terminology.md#6-extracting-with-a-schema-step-060) (or a past schema) → the one of the ground truth schema it translates to, both definitions as the row stores them, a made-up example for a predicate (`A CARRIES B → B ABOARD A`), and whether the row is checked. A ⚑ marks a row whose ground truth schema definition changed since it was checked (stale, see [row state](../docs/terminology.md#7-evaluating-extraction-step-070)). The same tabs, search and filters, plus the annotation tool's choice of rows by what they translate to.
- **Questions**: the open questions of `annotations/questions_for_experts.md`, most urgent first, grouped by priority (*High priority*, *Medium priority*, *Low priority*, each with its count), each in two parts. At the top, only what the expert needs to answer, in plain sections: one heading (its id and short title), its priority (and its status, unless open), the question, its context, the one record it shows as its example (*An example*: its title and notes in full, the words the question is about highlighted, the classed triples I wrote down from them), the definitions, rows and rules it is judged by, quoted, the options as plain choices, my current reading, and a box for the expert's answer. At the very bottom, folded and quiet, my bookkeeping, marked as not needed to answer: *The answer to this question impacts:* what the question is about (its topic and question kind), my notes, what each option would change (its consequences), everything the answer may change (its Affects: every record with its pool position, title and id, every classed triple, row, entry, rule and pipeline method), the pipeline's words it quotes, and the example's pool position and id. A search box (the questions, their records and options), a choice of priority (each with its count), *Show answered and withdrawn questions too* (hidden at first), and the same filters as the other lists. A term's first use in a question links to its row in the Terms view: where the question links it to `docs/terminology.md`, and, for the other terms the Terms view shows, where its words first appear outside a quote; the terms that are also everyday words (`LINKED_ONLY_WHERE_MARKED` in `helpers/review_page.py`: kind, domain, range, row, step, text, fact, model, pool, pair) only where the question links them.
- **Terms**: the terms the page uses, copied from `docs/terminology.md` when the page is made (the list is `GLOSSARY` in `helpers/review_page.py`; a term missing from terminology.md stops the page from being made, so no definition is ever written twice).

The questions and both lists can be shown all at once or one at a time (the ↑ and ↓ keys go through them; the questions in priority order). Wherever the files write an arrow as `->` (a pattern, an `only:` line, the notes), the page shows →; only the screen changes: the files, the data inside the page, and the comments' texts and emails keep `->`.

## How comments come back

1. A reviewer types in the box under any question, entry or row, or in *General comments*, and their name. Each comment is kept in their browser as they type (localStorage, on their computer only), so they can stop and come back; the top of the page counts the comments written. If the browser doesn't let the page keep them (some private windows), the page says so, and they must send or download before closing.
2. **Email my comments to Iulia** opens their email program with a new email to me, its body all their comments, for them to send (below). It needs an email program set up for `mailto:` links in their browser; without one, nothing opens, and the page tells them to use the next button instead.
3. **Download my comments** is the backup: it saves a small CSV file (UTF-8), one row per comment, for them to attach to an email to me. Its name is the standard `comments_<reviewer>_<YYYY-MM-DD>.csv` (the reviewer's name with each character other than a letter, digit, `_` or `-` made `_`, and the day it was saved), e.g. `comments_Jane_Smith_2026-10-24.csv`. Its columns: `reviewer`, `page_version`, `git_commit`, `kind` (`general`, `question`, `entity class`, `predicate`, or `translation row`), `entry` (the component class, or for a row its kind and the current schema's component class, e.g. `predicate CARRIES`, plus ` (line N)` for a second row of the same one; for a question its id, e.g. `Q1`; `(general)` for a general comment), `entry_text_shown` (the entry as the page showed it when the comment was written, so the comment still makes sense after the entry changes; for a question, its id, short title and the fingerprint of its words, e.g. `Q1: Should SpatialRepresentation be a closed list? | fingerprint 9ce614305731`), `comment`, and `timestamp`.
4. I save each email (Gmail: **⋮ → Download message**, which saves an `.eml` file), or paste its text into a `.txt` file, or save the attached CSV file (an `.eml` file with the CSV file attached is read whole, too), in `annotations/reviews/`, as it is.
5. `py helpers/review_page.py --read` reads every `.csv`, `.eml` and `.txt` file there (or the files and folders named) and writes a summary to `outputs/review/comments_<date>_<time>.md`, also printed: grouped into general comments, questions (each under its id and short title), entity classes, predicates and rows of the translation table, then by entry, each comment with its reviewer, date, page version and sender. Each comment's state, and every problem a file can have: *What --read reports*, below. One reviewer's comment on one entry counts once, the latest: a reviewer who sends twice sends the same comments twice. The annotation tool's **Reviewer comments** view shows the same comments, read by the same code ([annotations/README.md](../annotations/README.md), *Reading reviewers' comments*).

### What --read reports

**Each comment's state** against the files as they are now (`comment_state`, `COMMENT_STATES` in `common/common_helpers/review_comments.py`): exactly one of four, the first that applies, in this order.

| State | When | In the summary |
|---|---|---|
| `general` | A general comment (kind `general`). | Under *General comments*, no flag. |
| `gone` | Its entry (its kind and entry) is no longer in the files: an entity class or predicate no longer in `annotations/ground_truth_schema.txt`, a row no longer in the translation table, or a question no longer in `annotations/questions_for_experts.md`. A comment of a kind the page doesn't have is `gone` too (listed apart, under *Comments of an unknown kind*). | ⚑ *No longer in the files*, with the entry as the page showed it. |
| `changed` | Its entry reads differently now from how the page showed it when the comment was written. Spaces don't count, since an email program may wrap a line. A question counts as changed when any of its words do, except its status and priority lines and its answer. | ⚑ *Changed since that page*, with the entry then and now. |
| `unchanged` | Any other comment. | No flag. |

**Every problem a file can have**, listed at the top of the summary (*Files skipped, and what is missing*) and of the annotation tool's Reviewer comments view:

1. A `.csv` file, or a `.csv` file attached to an email, that lacks one of the columns above: skipped.
2. An `.eml` file whose From address isn't of an allowed domain (*Who sent it*, below): skipped, its sender named.
3. An `.eml` file from an allowed address with no review comments in it (no line `REVIEW COMMENTS (format 1)` in its text, and no `.csv` file attached that could be read): skipped. An email with no text and nothing attached is skipped without a problem.
4. A `.txt` file with no line `REVIEW COMMENTS (format 1)`: skipped.
5. A file that can't be read (the error is named): skipped.
6. A sending with a part missing: the comments in that part aren't read.
7. A part without its end line `=== end of part … ===` (cut short, or not copied whole): read, but a comment at its end may be incomplete.
8. Incomplete comments: a comment cut by a missing or cut-short part, or without its `[kind]` or `[entry]` line: left out, and counted.
9. The questions file not in its format: every comment on a question is then `gone`.

How they relate: 1 to 5 are about one file. 2, 4 and 5 each exclude every other of 1 to 5 for that file; an `.eml` file can have 1 (once per `.csv` file attached that lacks a column) and 3 together. 6 to 8 are about one sending, its parts put back together from any files; a sending can have all three. 9 is about the questions file, at most once per reading. A comment with no words is dropped, without a problem.

### The email

The page writes the email itself; the reviewer only presses Send. Its subject is `Review comments — <reviewer> — <page version>`, and its body is plain text, one field per line, that `--read` reads back even after an email program has wrapped long lines (at a space), quoted them in a reply (`> `), merged lines, or added a note before or a signature after:

```
REVIEW COMMENTS (format 1): please send this email as it is
[reviewer] Jane Smith
[page_version] review_2026-10-24_abc1234
[git_commit] abc1234
[sent] 2026-10-24T14:05:09-04:00
[part] 1 of 1
=== start of part 1 of 1 ===

=== comment ===
[kind] entity class
[entry] Instrument
[page_version] review_2026-10-24_abc1234
[git_commit] abc1234
[timestamp] 2026-10-24T10:00:00-04:00
[entry_text_shown] Instrument: a device that takes measurements
[comment] Also "sensor", maybe.
[comment] (a second line of the same comment)

=== end of part 1 of 1 ===
```

A line that starts with none of the `[field]` names continues the line before it, joined with one space; a comment's own line breaks are its `[comment]` lines. (A line an email program broke after a hyphen, not at a space, comes back with a space after the hyphen.) The whole format is `EMAIL_FORMAT` in `common/common_helpers/review_comments.py`.

**Length.** A `mailto:` link carries the email in the link itself, and links that are too long fail to open: Windows passes on at most 2,083 characters (`INTERNET_MAX_URL_LENGTH`, the limit of Internet Explorer and of Windows' own handling of links, through which Outlook and other email programs on Windows get them). The page keeps each link to 1,900 characters (my margin), counting the address, the subject, and the body as the link encodes it (a space takes 3 characters, an accented letter 6). Comments that don't fit in one email are split into numbered emails, `part 1 of N` in the subject and in the body, cut at line ends (or inside a long comment, at a space); the page then shows one button per part, each marked ✓ once pressed, and `--read` puts the parts of one sending back together, in order, from any files. A missing part is named in the summary, and the comment it cut is left out. More than 5 emails is too many to ask of a reviewer: the page then asks them to press Download my comments and attach the file instead, with a button that opens a short email to me to attach it to.

**The address** is my Gmail address with `+kgreview` before the `@`, which Gmail delivers to the same inbox and which lets me filter these emails, or block only that address if it is ever spammed. It is written in full nowhere in the repository or on the page: the page's script holds it in split parts and puts them together only when a button is pressed, so programs that collect addresses from web pages and repositories don't find it.

**Who sent it.** `--read` reads an `.eml` file only if its From address is of `nasa.gov` or a subdomain of it (e.g. `ndc.nasa.gov`; not `notnasa.gov`, not `nasa.gov.evil.com`), and lists every other one it skipped, with its sender. The domains are one setting, `ALLOWED_SENDER_DOMAINS` in `common/common_helpers/review_comments.py`. A `.txt` file of pasted text, or a CSV file, has no sender to check: its comments are read, marked *sender not verified* in the summary and in the annotation tool. A From address can be forged, so this is a filter, not proof: a forged comment would still only reach me, and I read every comment before acting on it.

**My Gmail filters** (in each, `<my address>` stands for my Gmail address with `+kgreview` before the `@`; Gmail: Settings → *Filters and Blocked Addresses* → *Create a new filter*, the words below in *Has the words*):

1. `to:(<my address>) from:(nasa.gov)` → **Apply the label** *KG reviews* and **Never send it to Spam**.
2. `to:(<my address>) -from:(nasa.gov)` → **Skip the Inbox (Archive it)**, or **Delete it**.

Gmail's `from:(nasa.gov)` matches any sender whose address contains those words (`notnasa.gov` too), so the filters sort; `--read`'s own check above is the stricter one.

## Where the comments stay

`annotations/reviews/` holds what reviewers sent: their names, their words, their email addresses. The repository is public, so `.gitignore` keeps everything in that folder out of Git except its README: the files stay on my computer only (back them up with the rest of my files, not with Git). The page tells reviewers that their name and comments reach only me, and are not put in the project's public repository. Nothing goes into that folder but what reviewers sent.

## Sending a newer copy

Comments are filed by entry (its kind and component class, or a question's id), not by page, so they carry over: a reviewer who opens a newer copy (the same link, after an update) in the same browser finds their comments under the same entries, and a comment written when the entry read differently says so under its box. The page also remembers the entries of the copies a reviewer opened before (up to three), and marks each entry that changed since the copy opened before it (⚑ *changed since you last looked*, the old text on hover) or is new. Comments on entries the newer copy no longer has are listed under *How to read this*, and stay in what they send. In another browser or on another computer, **Load my comments from a file** reads a downloaded comment file back in.

## The questions file

`annotations/questions_for_experts.md` is the questions' one home: I write and change them there, and nowhere else. One question per decision an expert's answer would settle: a new doubt that one answer would settle goes into that question (a new lettered sub-question, and its records and classed triples under *Affects*), not into a question of its own. A question keeps its number for good, since comments are filed under it; one I no longer ask becomes `withdrawn`, not deleted.

Everything before the first `## ` heading is the file's own introduction, not read. Each question is a section, its parts in this order (the parser: `common/common_helpers/expert_questions.py`):

```
## Q<n>: <short title>
- status: open | answered | withdrawn
- priority: high | medium | low
- question kind: records and triples | schema entry | rule | translation table rows | pipeline method | general
- topic: <a few words>
                                  for the expert: what they need to answer
### The question                  required: prose
### Context                       optional: prose
### Example record                at most one: the clearest example (below)
### Ground truth schema           optional: - entity class <EntityClass>: <its definition> / - predicate <PREDICATE>: <its definition>
### Translation table             optional: - <entity class|predicate> <component class> -> <component class or (none)>[ (swap subject and object)]: <the row's definition, current or past schema>
### Annotation guidelines         optional: - <section of the guidelines>, rule <n>: <the rule's words>
### Options                       optional: #### Option <k>: <title>, then prose: the choice, in plain words
### My current reading            required: prose, short
### The answer                    when answered, and only then: prose
                                  for me: my bookkeeping, folded at the bottom of the page
### My notes                      optional: prose (what I have annotated, pool positions, what the ground truth does meanwhile, pending facts)
### Consequences                  with Options, and only then: #### Option <k>: <the same title>, one "- " item each
### Affects                       required: one field per thing the answer may change (below)
### Pipeline method               optional: - <path in the repository>: <words quoted from that file>
```

**For the expert, and for me.** The parts down to *The answer* are all the expert reads to answer: the question, its context, the example, the definitions, rows and rules it is judged by, the options as plain choices (what the expert picks from, or comments on, without what each would change in my files), and my current reading. Everything that is my bookkeeping goes in the parts after it, which the page folds at the bottom of the question, under *The answer to this question impacts:*: which records I have annotated, pool positions and ids, what the ground truth does until the answer comes, a pending fact (added if the answer says so), what each option changes in the pipeline, the ground truth, the translation table or the scores, and every record, classed triple, row, entry, rule and pipeline method the answer may change. What the expert reads never says "pool position" or a record id: another record is named by its title, in quotes, after the word "record" (`the record "MODIS/Aqua Snow Cover 5-Min L2 Swath 500m V061"`), with its own words quoted when the expert needs them, and a triple is written out with its subject, predicate and object (`"Aqua" (Spacecraft) FLIES_IN "A-train" (SatelliteFormation)`).

**priority**: how much the answer matters now; the page shows `high` first. **question kind**: what the question is about: records and their classed triples; an entity class or predicate of the ground truth schema; a rule of the annotation guidelines; rows of the translation table; a method of the pipeline; or `general`, an idea with no record or classed triple of its own (its context is then the definitions, rules or method it concerns, quoted).

**Affects** lists everything the answer may change, one field each: `record at pool position <n>: <record id>`; `classed triple of the record at pool position <n>: "<subject instance>" (<SubjectClass>) <PREDICATE> "<object instance>" (<ObjectClass>)`; `translation table row: <entity class|predicate> <component class, current or past schema>`; `ground truth schema entry: <entity class|predicate> <component class>`; `rule: <section>, rule <n>`; `pipeline method: <path>: <what of it>`. It must be complete: a ground truth schema entry it names brings every ground truth triple of a tuning record that uses it, and every row of the translation table that translates to it, and a classed triple brings its record. The annotation tool shows, in **About this record**, the open questions whose Affects names the record (*Questions for experts*, each with the record's classed triples it names on hover), and the Reviewer comments view shows each question's title and Affects.

**The example record**: at most one, the clearest for the decision, with its fields `record id`, `pool position`, `title`, `notes` (each in full), `source text` (one or more: the passages the question is about), `classed triple` (its ground truth triples concerned), and, for a record not in the ground truth yet, `in the ground truth: not yet: <why>` (its classed triples are then my drafts, not checked). The page shows its title and notes, with the source texts highlighted, and its classed triples; its record id and pool position only at the bottom. Other records are named in the prose by their titles (above), and all of them are in Affects.

A field is a line `- <label>: <value>`; a line indented by two spaces continues it (a blank line between two such lines is a paragraph break, as in a record's notes). Prose is paragraphs, `- ` lists, and tables (a header line, a line of dashes, the rows), with `` `code` ``, `**bold**`, `*italic*` and links (the words in square brackets, the address in parentheses after them); a link to `docs/terminology.md` marks a term (the page links it to its Terms view, and refuses one the Terms view doesn't show).

**Checked each time the page is made** (it refuses, naming the line, and nothing is published): the format; every record is a tuning record at its pool position (030's `splits.json`: a held-out record is refused, since an expert's answer about it would let it influence the pipeline); its title and notes are the record's (020's `records.jsonl`, spaces aside); each source text is in its title or notes, word for word; each classed triple is one of its ground truth triples, with that source text among the record's; each definition is the ground truth schema's now; each row is the translation table's (target, swap, definition); each rule's words are in that rule of `annotations/guidelines.md`; each pipeline method's words are in its file; Affects is complete (above); what the expert reads says no "pool position" and no record id; each title after the word "record" there is, spaces aside, the title of a record Affects names; and *Consequences* has the options of *Options*, the same numbers and titles. So a quote never drifts from its source: change the source, and the page says which question to update.

## What it can't do

- It can't change anything: no server of mine, nothing sent by the page itself, no file written except the reviewer's own download; an email goes only when the reviewer presses Send in their email program. A reviewer's suggestions reach the files only through me.
- It shows the ground truth schema's patterns as its file lists them, not the patterns the ground truth itself uses (the annotation tool's **Help → Ground truth schema** shows those).
- It doesn't know which rows of the translation table the current schema still uses: it shows every row, with the definitions the row stores.
- Comments kept in a browser are lost if the reviewer clears its site data before sending or downloading.
