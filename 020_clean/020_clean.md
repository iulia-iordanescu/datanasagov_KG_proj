# 020_clean

Terms ([record](../docs/terminology.md#1-records-and-their-text), [metadata field](../docs/terminology.md#1-records-and-their-text), [maintainer](../docs/terminology.md#1-records-and-their-text), [text](../docs/terminology.md#1-records-and-their-text), …) are as defined in [docs/terminology.md](../docs/terminology.md), especially section *Records and their text*.

## Purpose

Turns the raw catalog [records](../docs/terminology.md#1-records-and-their-text) saved by 010 into clean records that every later [step](../docs/terminology.md#8-the-pipeline) reads. Four things happen:

- **Each catalog entry is kept once.** A record whose id already appeared earlier in the [harvest](../docs/terminology.md#1-records-and-their-text) is dropped, keeping the first copy. This happens when the catalog changes during a harvest and CKAN's pages shift (see 010's warning about records that appear twice). The full harvest of 2026-09-27 had 12 such repeats, each identical to its first copy. A record with no id at all is dropped too; the 2026-09-27 harvest had none.
- **[Text](../docs/terminology.md#1-records-and-their-text) is cleaned.** Some `notes` values, and a few titles, carry HTML tags or escapes (`&lt;p&gt;`, `&amp;rsquo;`, `<sub>2</sub>`, links): in the 2026-09-27 harvest, 1,277 of 36,375 `notes` values and 6 titles. Sent to a [model](../docs/terminology.md#8-the-pipeline) as is, they would produce [triple instances](../docs/terminology.md#2-triples) and [classed triples](../docs/terminology.md#2-triples) about `<p>` tags rather than about what the records describe. It becomes plain text, and each value is checked so that no word, number or URL is lost. Every text value also has its whitespace tidied, and a title is made one line: in the 2026-09-27 harvest, 3,356 titles had line breaks, runs of spaces or non-breaking spaces inside (e.g. `ROSETTA-ORBITER 67P RSI 1/2/3`, a line break and 37 spaces, `COMET ESCORT …`), which the catalog's web page hides but a file keeps. Descriptions keep their line breaks: they separate paragraphs.
- **[Maintainer](../docs/terminology.md#1-records-and-their-text) spellings are joined.** "Kristan Morgan" and "KRISTAN MORGAN" become one maintainer. 030 orders each maintainer's records apart, 040 learns from the largest maintainers, and 080 will make one [node](../docs/terminology.md#8-the-pipeline) per maintainer, so one person must not count as two.
- **Each [field](../docs/terminology.md#1-records-and-their-text) gets its own key.** Title, notes, maintainer, tags, formats and the rest are stored separately, so no later step has to guess where a title ends and a description begins.

Apart from records with no id and later copies of a repeated id, every record is kept, even one with no title or notes: the graph needs every catalog entry, and its structured fields still hold [facts](../docs/terminology.md#2-triples).

## To do

### Every step

- **Run it** after the [steps](../docs/terminology.md#8-the-pipeline) before it, and again whenever their outputs change (see *How to run*).
- **Before a step pays for [model calls](../docs/terminology.md#8-the-pipeline),** read what it prints: anything it can't do exactly as asked is listed above the question. Then press Enter to go ahead, or anything else to stop, having spent nothing. (Steps that call no [model](../docs/terminology.md#8-the-pipeline) don't ask.)
- **Read the [report](../docs/terminology.md#8-the-pipeline)'s Warnings:** the report is `outputs/reports/<step>_<date>_<time>.md` (the step prints its path when it ends). Each warning is explained, with what to do, in *Checks and warnings* below.
- **Commit every changed file in the `annotations/` folder to Git,** so your work is safe.

### This step

- Nothing else: the [step](../docs/terminology.md#8-the-pipeline) runs on its own.

## Inputs

| Input | Default | Contents |
|---|---|---|
| `batches` | `010_harvest/batch_*.json` | Every [batch file](../docs/terminology.md#1-records-and-their-text) 010 saved: raw CKAN [records](../docs/terminology.md#1-records-and-their-text), each file with the request that returned it. Files in 010's old format (a bare list of records) stop the [step](../docs/terminology.md#8-the-pipeline). |

## Outputs

In `outputs/intermediate_results/020_clean/`:

**On a rerun:** `records.jsonl` is replaced.

| File | Contents |
|---|---|
| `records.jsonl` | One cleaned [record](../docs/terminology.md#1-records-and-their-text) per line, in [harvest](../docs/terminology.md#1-records-and-their-text) order ([batch files](../docs/terminology.md#1-records-and-their-text) in order, records in their order within each file). |
| `_manifest.json` | [Run id](../docs/terminology.md#8-the-pipeline), [settings](../docs/terminology.md#8-the-pipeline), input files and their hashes, output files and their hashes, headline numbers and the [harvest date](../docs/terminology.md#1-records-and-their-text). Written when a [run](../docs/terminology.md#8-the-pipeline) finishes. |

One record:

```json
{"id": "a1b2…", "name": "modis-aqua-…", "title": "MODIS/Aqua …", "notes": "MODIS aboard Aqua …\nlink [https://…]",
 "maintainer": "Kristan Morgan", "maintainer_as_harvested": "KRISTAN MORGAN",
 "organization": "NASA", "tags": ["earth science"], "formats": ["HDF", "CSV"],
 "license": "…", "url": "…", "metadata_created": "…", "metadata_modified": "…",
 "_cleaning": {"title": "parsed", "notes": "parsed"},
 "_origin": ["010_harvest/batch_00000.json#a1b2…"]}
```

| Field | Meaning |
|---|---|
| `id` | The CKAN record id, surrounding spaces removed. Every later [step](../docs/terminology.md#8-the-pipeline) tells records apart by it. |
| `name` | CKAN's short name for the record (the last part of its web address). |
| `title`, `notes` | The record's title and notes, cleaned; the title on one line, with single spaces. Always saved; `""` when the catalog gives none. |
| *extra text fields* | Only if `extra_text_fields` names any: each one cleaned like `title` and `notes`, under its own name, right after `notes`. |
| `maintainer` | One name per [maintainer](../docs/terminology.md#1-records-and-their-text), spellings joined. Runs of spaces inside the name are collapsed to one. A missing or blank maintainer becomes `undefined`, a value the catalog itself uses (989 records on 2026-09-27; no record had a blank one). |
| `maintainer_as_harvested` | The maintainer exactly as the catalog gives it (`""` when it gives none), so every join can be checked. |
| `organization` | The organization's title, or `null`. |
| `tags` | Tag names, in the catalog's order. |
| `formats` | The file formats of the record's resources: each listed once, surrounding spaces removed, blanks left out, spelled as the catalog writes them. |
| `license`, `url`, `metadata_created`, `metadata_modified` | As the catalog gives them (`license` is CKAN's `license_title`). |
| `_cleaning` | Which method cleaned each text field (see How it works). |
| `_origin` | The batch file and record the item came from (see `helpers/audit.md`). |

Each run also leaves `outputs/reports/<run id>.md` (the [report](../docs/terminology.md#8-the-pipeline): what it read and wrote, its numbers, its warnings) and `outputs/logs/<run id>.log` (everything it did, line by line); how to read them: `helpers/audit.md`.

## Settings

| Setting | Default | What it does | When to change it |
|---|---|---|---|
| `extra_text_fields` | empty | Free-text [fields](../docs/terminology.md#1-records-and-their-text) of the raw [record](../docs/terminology.md#1-records-and-their-text) to clean and save besides `title` and `notes`, separated by spaces. `title` and `notes` are always cleaned and saved; naming them here changes nothing. A name 020 already uses for a field of its own (e.g. `maintainer`, `tags`) stops the [step](../docs/terminology.md#8-the-pipeline), since it would overwrite that field. | To bring in another text field, e.g. `author`. |
| `join_maintainers` | true | Join spellings of one [maintainer](../docs/terminology.md#1-records-and-their-text) into one name. | Set to `false` to keep each spelling as harvested (a missing or blank one still becomes `undefined`), e.g. to check the joins. |

## How to run

From the repository folder, with the environment active (`docs/virtual_environment_setup.md`):

```
py 020_clean/run.py --help                              every input and setting, with its default
py 020_clean/run.py                                     reads 010's batch files
py 020_clean/run.py --join_maintainers false            keep maintainer spellings as harvested
py 020_clean/run.py --extra_text_fields author          also clean and save the author field
py 020_clean/run.py --batches path/to/batch_*.json      read batch files from elsewhere
```

**Paying.** This [step](../docs/terminology.md#8-the-pipeline) makes no [model calls](../docs/terminology.md#8-the-pipeline): it costs nothing, and keeps no cache.

The whole catalog took 14–32 s (36,387 [records](../docs/terminology.md#1-records-and-their-text) read; 2026-09-27 to 2026-09-29). A rerun replaces `records.jsonl`.

## How it works

Four [stages](../docs/terminology.md#8-the-pipeline), in `020_clean/run.py`'s `main()`, all code:

1. **Load the raw [records](../docs/terminology.md#1-records-and-their-text)** (`load_raw`). First the `extra_text_fields` [setting](../docs/terminology.md#8-the-pipeline) is checked (see Settings), so a name that would overwrite another [field](../docs/terminology.md#1-records-and-their-text) stops the [step](../docs/terminology.md#8-the-pipeline) before any file is read. Then every [batch file](../docs/terminology.md#1-records-and-their-text) is read in order. A record with no id is dropped, and named in the [log](../docs/terminology.md#8-the-pipeline) and the [report](../docs/terminology.md#8-the-pipeline) by its batch file, position, CKAN name and title: an id made up from its position would point at a different record after a re-harvest, and [ground truth](../docs/terminology.md#4-ground-truth-and-samples) written under it would be evaluated against the wrong [text](../docs/terminology.md#1-records-and-their-text). A record whose id was already seen is dropped too, keeping the first copy.
2. **Keep the fields** (`keep_fields`). Each record becomes one line with each field under its own key (see Outputs), and its [origin](../docs/terminology.md#8-the-pipeline): the batch file and the record's id there.
3. **Clean the text** (`clean_text`). First the cleaning library runs its own regression cases, and the step stops if any fails. Then each text field is cleaned:
   - A value with no `<` and no `&` in it has no markup to remove, so it is only tidied: spaces at the end of each line and at either end of the value are removed, and runs of blank lines are cut to one. It is counted as *parsed*. This is most values: 36,071 of 36,375 titles and 33,909 of 36,375 descriptions on 2026-09-27.
   - Any other value is decoded (`&amp;lt;` → `&lt;` → `<`: up to 3 passes, stopping when nothing changes, since some sources escape twice) and cleaned by the first of three methods whose result passes the check that every run of letters and digits in the input (words, numbers, URL fragments) is still there, as many times:
     - *parsed*: an HTML parser reads the markup and rebuilds the text. Links keep their address as `text [URL]`; a link whose text is its own address is written once, not as `URL [URL]`. Subscripts become `_x`, list numbering is kept, and each row of an HTML table goes on one line with ` | ` between cells. A table typed as plain text (`| a | b |` on each line) keeps its lines.
     - *conservative*: a cruder method that removes anything shaped like a tag. Used when the parser would lose content, e.g. on a broken attribute quote.
     - *source*: the decoded value, with its markup left in. It cannot lose anything, because it is the input.

   Then every title is made one line: each [run](../docs/terminology.md#8-the-pipeline) of line breaks and spaces inside it (non-breaking spaces included) becomes one space. The report says how many titles changed.
4. **Join [maintainer](../docs/terminology.md#1-records-and-their-text) spellings** (`join_maintainers`). First the joining rules run their own checks (`selftest()` in `maintainers.py`), and the step stops if any fails. Then two spellings are one maintainer when they have the same words once case, punctuation, spacing and word order are ignored, and so are the degree Ph.D (however it is written: PhD, Ph.D., PH. D, Ph D) and the honorifics Dr, Mr, Ms, Mrs and Prof as whole words. Every other word counts: names differing by a middle name or an initial ("Lola Olsen", "Lola M. Olsen"; "John Smith", "John D. Smith") stay apart, and so do names differing by Jr. or Sr. Joined spellings are written in "John Doe" form: degree and honorifics dropped; a spelling that is already mixed case is preferred, so acronyms such as NASA survive; a name written only in capitals is title-cased. A maintainer written only one way keeps its spelling. Before any comparison, runs of spaces inside a name are collapsed to one and spaces at either end removed, so `Parnchai  Sawaengphokhai` (two spaces) is not a spelling of its own. On 2026-09-27: 434 spellings, 422 maintainers after joining.

**Then the results** (`results`): `records.jsonl` is written under a temporary name and renamed when complete. The report gives record counts; per text field, how many values had HTML tags or escapes and which cleaning method each value got; the joins made; and the 10 largest maintainers. Records dropped for having no id are all listed. Other lists (repeated ids, values that needed a fallback method, joins) show their first 20 entries and say how many more there are; every repeated id and every fallback value also has a DEBUG line in the log.

The code: `020_clean/` holds `run.py` (the [control panel](../docs/terminology.md#8-the-pipeline): inputs, settings and the [moves](../docs/terminology.md#8-the-pipeline), in order); `020_clean/020_clean_helpers/` holds `moves.py` (the moves, and writing the results), `note_cleaning.py` (the cleaning library and its self-test) and `maintainers.py` (the joining rules and their self-test). Shared with other steps: `common/common_helpers/records_io.py` (the text fields), `common/common_helpers/files.py` (saving files). Both self-tests also run on their own: `py note_cleaning.py --selftest` and `py maintainers.py`, from inside `020_clean/020_clean_helpers/`.

## Prompts

None: this [step](../docs/terminology.md#8-the-pipeline) makes no [model calls](../docs/terminology.md#8-the-pipeline).

## Checks and warnings

**Shown before paying:** none, since this [step](../docs/terminology.md#8-the-pipeline) makes no [model calls](../docs/terminology.md#8-the-pipeline).

**In the [report](../docs/terminology.md#8-the-pipeline)**, under *Warnings*:

| Message | Meaning | What to do |
|---|---|---|
| *N records have no id and were dropped* | The catalog returned [records](../docs/terminology.md#1-records-and-their-text) with no id. Every one is listed in the report under *What this run worked on* ([batch file](../docs/terminology.md#1-records-and-their-text), position, CKAN name, title) and in the [log](../docs/terminology.md#8-the-pipeline) (a DEBUG line each). | Look at them in the batch files. None were found on 2026-09-27. |
| *N text values could not be cleaned without losing content* | Both cleaning methods lost content, so the value was kept as decoded, markup included (the *source* method). Their ids are in the report under Cleaning. | Look at those records. If the markup matters, add a case to `SELFTESTS` in `note_cleaning.py` and improve the cleaner. |
| *Every record has the same maintainer* | 040 would learn the [schema](../docs/terminology.md#3-schemas) from one [maintainer](../docs/terminology.md#1-records-and-their-text) only. Checked only when `join_maintainers` is on. | Check the [harvest](../docs/terminology.md#1-records-and-their-text): usually a sign of a broken or trial harvest. |
| *N of M records have no origin* | Should never happen. | A code change broke `keep_fields`; fix it before using the output. |

**The step stops** with:

| Message | Meaning | What to do |
|---|---|---|
| *… is in the old batch format* | 010's files were saved by an older version, without a [request block](../docs/terminology.md#1-records-and-their-text). | Rerun `py 010_harvest/run.py`, which downloads them again. |
| *extra_text_fields names …, which 020 already writes as a field of its own* | An extra text [field](../docs/terminology.md#1-records-and-their-text) was given the name of a field 020 already writes, e.g. `maintainer`. | Remove that name from `extra_text_fields`. |
| *AssertionError: N failure(s)* | A self-test failed: the cleaning library's (in `clean_text`) or the joining rules' (in `join_maintainers`). The timeline in the report shows which [move](../docs/terminology.md#8-the-pipeline) failed. | Don't use the output. Read the listed failures; usually a changed Python version, or an edit to `note_cleaning.py` or `maintainers.py`. |
| *missing input files … (run 010_harvest first, or pass --batches)* | An input file isn't there: usually an earlier step hasn't run. | Run the steps in order, or pass the file with `--<input>`. |

Values cleaned by the *conservative* method are complete but may read less well; the report lists their ids as worth a look (2 descriptions on 2026-09-27).

## Audit trail

- **[Log](../docs/terminology.md#8-the-pipeline).** `outputs/logs/<run id>.log` records the command line, the [settings](../docs/terminology.md#8-the-pipeline), the git commit, each [move](../docs/terminology.md#8-the-pipeline)'s duration, each output file's hash and, on failure, the full traceback.
- **[Origin](../docs/terminology.md#8-the-pipeline).** Each [record](../docs/terminology.md#1-records-and-their-text)'s `_origin` names the 010 [batch file](../docs/terminology.md#1-records-and-their-text) and the record's id there, e.g. `010_harvest/batch_00000.json#a1b2…`.
- **Trace.** `py helpers/audit.py <record id>` follows a record back through every [step](../docs/terminology.md#8-the-pipeline)'s output to the 010 batch file and the API request that first returned it (`helpers/audit.md`).

## Known limits

- **Middle names, initials and Jr./Sr. aren't joined.** "Lola Olsen" and "Lola M. Olsen" stay two [maintainers](../docs/terminology.md#1-records-and-their-text), even if they are one person: joining them needs a rule someone would have to choose, and joining two people is worse than keeping one person's spellings apart.
- **A maintainer written only one way is left as written**, titles and capitals included: e.g. `DAVID, DR. DINER`, `Dr. Natalia Papitashvili`. Only joined names are rewritten in "John Doe" form.
- **Formats and tags are not normalized.** They are copied as the catalog spells them; nothing would join `csv` and `CSV`. On 2026-09-27 no format was spelled two ways by case, and no [record](../docs/terminology.md#1-records-and-their-text) listed a tag twice.
- **Only the text [fields](../docs/terminology.md#1-records-and-their-text) are cleaned.** Tags, formats and the other structured fields are not checked for HTML.
- **A repeated id keeps its first copy.** If the catalog changed the record between the two pages, the later version is lost; only a fresh [harvest](../docs/terminology.md#1-records-and-their-text) fixes that. On 2026-09-27 all 12 pairs were identical.
