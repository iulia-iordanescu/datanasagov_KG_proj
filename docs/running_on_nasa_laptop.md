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

Create the file `.env` with your Ask Sage email and key: part 6 of `docs/virtual_environment_setup.md`.

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
| 070 evaluate | `py 070_evaluate.py` | not yet measured | one call, only when 060's schema has names not yet in `annotations/name_mapping.csv`; then check those rows and run it again |

Each step ends by printing where its report is (`outputs/reports/<run id>.md`). Read the report's **Warnings** before running the next step. Each step's guide (`instructions/<step>.md`) says what every warning means and what to do.

## 5. The steps that cost money: 040, 050, 060, 070

Each sends texts to the AI model, and each request is a paid call. Before its first call, each one prints its plan (how many calls, which model) and waits: **Enter** goes ahead, anything else stops, having spent nothing. If the run can't do exactly what you asked, it says so above that question. Its first call is a one-line test that your key and the model name work, so a mistake costs one call, not hundreds.

Try a tiny run of each first, to see that everything works and what a call costs:

```powershell
py 040_induce_schema.py --induction_maintainers 2 --texts_per_maintainer 2
py 050_annotate.py --records_per_batch 1
py 060_extract.py --ids <one finished ground truth record id>
```

Every model answer is kept in the step's `cache/` folder under `outputs/`, so the full run reuses the tiny run's answers and a rerun pays only for what changed. **Don't delete `outputs/`** unless you mean to pay for those calls again.

060 needs 040's schema, and by default extracts only from the ground truth records you've finished (next section). 070 makes a paid call only when the schema 060 used has names it can't translate yet: one call proposes translations, and 070 stops so you can check them in `annotations/name_mapping.csv`. Everything else about each step, including what each warning means, is in its guide, `instructions/<step>.md`.

## 6. Annotating ground truth (after 050, before 060)

```powershell
py annotate.py
```

A page opens in your browser: pick the draft batch 050 wrote, correct it, tick *All facts extracted* on each finished record, stop with Ctrl+C, commit. How: `annotations/README.md`. It makes no model calls, so it also works on your personal laptop, if that laptop has run steps 010 to 030 and has the draft batch.

## 7. If something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| *Test call to … failed* (040, 050, 060 or 070 stops) | The key, the model name, or the connection is wrong. Nothing else was called. | Check `.env`, that you're on NASA's network (or VPN), and `MODEL` in `common/llm.py`. |
| *Set ASKSAGE_EMAIL and ASKSAGE_API_KEY* | `.env` is missing or misspelled. | Section 3. |
| *Failed to resolve 'api.asksage.ai.nasa.gov'* | The laptop can't reach Ask Sage. | Connect to NASA's network or VPN. |
| *missing input files* | An earlier step hasn't run yet. | Run the steps in order (section 4). |
| *running scripts is disabled* | PowerShell's script policy. | Part 3 of `docs/virtual_environment_setup.md`. |

## 8. Tracing where something came from

Any record, triple instance or schema entry can be traced back to the API request that first returned it:

```powershell
py audit.py <record id>
```

See `instructions/000_audit.md`.

## Added later

*(New items go here.)*
