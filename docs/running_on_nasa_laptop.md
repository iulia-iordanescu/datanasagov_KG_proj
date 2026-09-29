# Running the pipeline on the NASA laptop

The code is built and tested on a personal laptop, which can't reach Ask Sage, the NASA service that hosts the AI model. Real runs happen on the NASA laptop, after pulling the code from GitHub. This page is the checklist for that. Items get added at the end as the pipeline grows.

Two things never travel through Git, on purpose:

- **`.env`**, which holds your Ask Sage key: a key in Git could be read by anyone who can see the repository.
- **`outputs/`**, everything a pipeline run produces: it's rebuilt by running the steps, and it's large.

So the NASA laptop needs its own `.env`, and makes its own `outputs/` by running the steps.

## 1. Get the code

In PowerShell, in the folder where the repository lives (or where you want it):

```powershell
git clone https://github.com/iulia-iordanescu/datanasagov_KG_proj.git     # first time only
cd datanasagov_KG_proj
git fetch
git switch design-refactoring
git pull
```

The work is on the branch `design-refactoring`, not `main`.

If Git then shows many files as changed although you didn't touch them, that's the line-ending rule (`.gitattributes`) settling in. Run this once, then check that `git status` is clean:

```powershell
git add --renormalize .
git status
```

## 2. Set up Python

Follow `docs/virtual_environment_setup.md`, with one difference: **install from the saved package list rather than saving a new one.** In short, from the repository folder:

```powershell
py -3.14 -m venv .myvenv
.\.myvenv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell says running scripts is disabled, see part 3 of the setup guide.

Every new PowerShell window needs `.\.myvenv\Scripts\Activate.ps1` again; your prompt then starts with `(.myvenv)`.

## 3. Add your Ask Sage key

Create a file named `.env` in the repository folder (part 6 of the setup guide), with your own values:

```
ASKSAGE_EMAIL=you@nasa.gov
ASKSAGE_API_KEY=your-key-here
```

`.gitignore` keeps it out of Git.

## 4. Run the steps, in order

Each step reads what the one before it wrote, so run them in this order. From the repository folder, with the environment active:

| Step | Command | Time (measured 2026-09-27/28) | Pays for model calls? |
|---|---|---|---|
| 010 harvest | `py 010_harvest.py` | about 23 min | no |
| 020 clean | `py 020_clean.py` | about 15 s | no |
| 030 split | `py 030_split.py` | about 3 s | no |
| 040 induce schema | `py 040_induce_schema.py` | not yet measured | **yes** |
| 050 annotate | `py 050_annotate.py` | not yet measured | **yes** (about one call per record) |
| 060 extract | `py 060_extract.py` | not yet measured | **yes** (about one call per record: by default only the finished ground truth records) |

Each step ends by printing where its report is (`outputs/reports/<run id>.md`). Read the report's **Warnings** before running the next step. Each step's guide (`instructions/<step>.md`) says what every warning means and what to do.

## 5. Step 040: the first run that costs money

040 sends each text to the AI model; each request is a paid call. Before its first call it prints its plan (how many calls, which model) and waits:

- press **Enter** to go ahead;
- type anything else to stop, having spent nothing.

Its first call is a one-line test that your key and the model name work, so a mistake costs one call, not hundreds.

**Try a tiny run first.** This learns from 2 texts from each of 2 maintainers (4 texts, so about 4 model calls to extract triple instances plus a few more to label, merge and define), which shows whether everything works and what a call costs:

```powershell
py 040_induce_schema.py --induction_maintainers 2 --texts_per_maintainer 2
```

Then the full run (150 texts):

```powershell
py 040_induce_schema.py
```

It reuses the tiny run's answers: every model answer is kept in `outputs/intermediate_results/040_induce_schema/cache/`, and a rerun pays only for what changed. **Don't delete `cache/`** (or `outputs/`) unless you mean to pay for those calls again.

The report's **Model calls** table counts each stage's calls exactly. Its **Merges** list is the one thing to check by eye: a wrong merge (two different ideas made one) is the one mistake code can't catch.

## 6. If something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| *Test call to … failed* (040 or 050 stops) | The key, the model name, or the connection is wrong. Nothing else was called. | Check `.env`, that you're on NASA's network (or VPN), and `MODEL` in `common/llm.py`. |
| *Set ASKSAGE_EMAIL and ASKSAGE_API_KEY* | `.env` is missing or misspelled. | Section 3. |
| *Failed to resolve 'api.asksage.ai.nasa.gov'* | The laptop can't reach Ask Sage. | Connect to NASA's network or VPN. |
| *missing input files* | An earlier step hasn't run yet. | Run the steps in order (section 4). |
| *running scripts is disabled* | PowerShell's script policy. | Part 3 of `docs/virtual_environment_setup.md`. |

## 7. Tracing where something came from

Any record, triple instance or schema entry can be traced back to the API request that first returned it:

```powershell
py audit.py <record id>
```

See `instructions/000_audit.md`.

## Added later

*(New items go here as steps are added.)*

### Annotating ground truth (step 050)

Each run of `py 050_annotate.py` drafts the next 10 records of the pool into one draft batch (`--records_per_batch 3` for fewer; `instructions/050_annotate.md` has the other settings). Like 040, it shows its plan and waits for Enter before paying, and if it can't do exactly what you asked (an id it can't find, fewer records than asked, …) it says so above that question. Try a tiny run first: `py 050_annotate.py --records_per_batch 1`.

The ground truth is the folder `annotations/ground_truth/`: one file per corrected batch. After each run of step 050, correct its draft batch with the annotation tool:

```powershell
py annotate.py
```

It opens a page in your browser. Pick the batch at the top: the tool copies the draft into `annotations/ground_truth/` itself (e.g. `drafted_triples_batch1.csv` → `batch_001.csv`) and saves every change there straight away. When you're done, stop it with Ctrl+C and commit the file. It needs no model calls, so it also works on your personal laptop, as long as that laptop has run steps 010 to 030 (the tool shows each record's text from their outputs) and has the draft batch. The full steps are in `annotations/ground_truth/README.md`.

### Extracting (step 060)

`py 060_extract.py` needs 040's schema, so run 040 first. By default it extracts only from the ground truth records you've marked finished in the annotation tool, about one model call each; like 040 and 050, it shows its plan and waits for Enter before paying. `--extract_from all` extracts from every record (about 36,000 calls): only once the schema is final. To add entity classes or predicates by hand (e.g. from your mentor), write them in `annotations/schema_additions.txt`; how, in `instructions/060_extract.md`.
