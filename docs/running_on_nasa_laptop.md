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
| *Test call to … failed* (040 stops) | The key, the model name, or the connection is wrong. Nothing else was called. | Check `.env`, that you're on NASA's network (or VPN), and `MODEL` in `common/llm.py`. |
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
