# Running the pipeline on the NASA laptop

The code is built and tested on a personal laptop, which can't reach Ask Sage, the NASA service that hosts the AI [model](terminology.md#8-the-pipeline). Real [runs](terminology.md#8-the-pipeline) happen on the NASA laptop, after pulling the code from GitHub. This page is the checklist for that. Items get added at the end as the pipeline grows.

Two things never travel through Git, on purpose:

- **`.env`**, which holds your Ask Sage key: a key in Git could be read by anyone who can see the repository.
- **`outputs/`**, everything a pipeline run produces: it's rebuilt by running the [steps](terminology.md#8-the-pipeline), and it's large.

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

Each [step](terminology.md#8-the-pipeline) reads what the one before it wrote, so run them in this order. From the repository folder, with the environment active:

| Step | Command | Time (measured 2026-09-27/28) | Pays for model calls? |
|---|---|---|---|
| 010 [harvest](terminology.md#1-records-and-their-text) | `py 010_harvest/run.py` | about 23 min | no |
| 020 clean | `py 020_clean/run.py` | about 15 s | no |
| 030 split | `py 030_split/run.py` | about 3 s | no |
| 040 induce [schema](terminology.md#3-schemas) | `py 040_induce_schema/run.py` | not yet measured | **yes** |
| 050 annotate | `py 050_annotate/run.py` | not yet measured | **yes** (about one call per [record](terminology.md#1-records-and-their-text)) |
| 060 extract | `py 060_extract/run.py` | not yet measured | **yes** (about one call per record: by default only the finished [ground truth](terminology.md#4-ground-truth-and-samples) records) |
| 070 evaluate | `py 070_evaluate/run.py` | not yet measured | **yes** (one call, only when the [current schema](terminology.md#6-extracting-with-a-schema-step-060) has [component classes](terminology.md#3-schemas) not yet in `annotations/component_class_mapping.csv`; then check those rows and run it again) |

Each step ends by printing where its [report](terminology.md#8-the-pipeline) is (`outputs/reports/<run id>.md`). Read the report's **Warnings** before running the next step. Each step's guide (`<step>/<step>.md`) says what every warning means and what to do.

## 5. The steps that cost money: 040, 050, 060, 070

Each sends [texts](terminology.md#1-records-and-their-text) to the AI [model](terminology.md#8-the-pipeline), and each request is a [paid call](terminology.md#8-the-pipeline). Before its first call, each one prints its plan (how many calls, which model) and waits: **Enter** goes ahead, anything else stops, having spent nothing. If the [run](terminology.md#8-the-pipeline) can't do exactly what you asked, it says so above that question. Its first call is a one-line test that your key and the model work, so a mistake costs one call, not hundreds.

Every model answer is kept in the [step](terminology.md#8-the-pipeline)'s `cache/` folder under `outputs/`, so a rerun pays only for what isn't there yet. **Don't delete `outputs/`** unless you mean to pay for those calls again.

### Test run first

The cheapest way to check that everything works, about 20 [paid calls](terminology.md#8-the-pipeline) in all:

1. **010, 020, 030: run them for real** (section 4). They cost nothing. Don't make a "quick trial" [harvest](terminology.md#1-records-and-their-text) (`--max_records`): 030 writes its file only once, so a trial catalog would stay in it until you delete `outputs/intermediate_results/030_split/splits.json`.
2. **040–070: tiny runs**, in order:

   | [Step](terminology.md#8-the-pipeline) | Command | Paid calls, roughly |
   |---|---|---|
   | 040 | `py 040_induce_schema/run.py --induction_maintainers 2 --texts_per_maintainer 2` | 10–15 (4 [texts](terminology.md#1-records-and-their-text), then labeling, merging, defining) |
   | 050 | `py 050_annotate/run.py --records_per_batch 1` | 2 (one [record](terminology.md#1-records-and-their-text), and the test call) |
   | 060 | `py 060_extract/run.py` | 3 (the finished [ground truth](terminology.md#4-ground-truth-and-samples) records, 2 as of 2026-10-01, and the test call) |
   | 070 | `py 070_evaluate/run.py` | 2 the first time ([component class](terminology.md#3-schemas) translations, and the test call); it then stops so you can check the rows it added to `annotations/component_class_mapping.csv`. Run it again: 0 calls. |

3. **Check you're charged properly.** For each [run](terminology.md#8-the-pipeline), compare the plan it prints before you press Enter ("… will make N [model call](terminology.md#8-the-pipeline)(s) …") with its [report](terminology.md#8-the-pipeline)'s *Model calls* table (`outputs/reports/<run id>.md`): calls per [stage](terminology.md#8-the-pipeline), the test call, and the total paid. Running the same command again should show 0 paid calls: the cache works, and nothing is paid twice.

Nothing is wasted: the real 040 run reuses the tiny run's extractions; 050's record is real work (correct it in `py helpers/annotate.py`); 060 and 070 simply run again after the real 040.

### Choosing a model

Each of 040–070 has a `model` [setting](terminology.md#8-the-pipeline) (default `google-claude-sonnet-5`). To see which [models](terminology.md#8-the-pipeline) Ask Sage lists for your account (free):

```powershell
py helpers/models.py
```

A listed model may still refuse you. To find out, just use it in a tiny [run](terminology.md#8-the-pipeline), e.g. `py 050_annotate/run.py --model <name> --records_per_batch 1`: if it refuses, the [step](terminology.md#8-the-pipeline) stops at its one-line test call, having spent that call only, and says why. Try the next one.

Which model where:

- **040, 050, 070: the strongest model that answers you.** Their calls are few (tens to a few hundred), and their quality matters most: 040 shapes the [schema](terminology.md#3-schemas), 050 decides how much you correct by hand, 070's translations decide the metrics.
- **050 and 060: two different models, from different makers if you can** (e.g. a Claude model for one, a Gemini or GPT model for the other). The [ground truth](terminology.md#4-ground-truth-and-samples) starts as 050's draft; if 060 used the same model, the [facts](terminology.md#2-triples) that model misses would be missing from both, and [recall](terminology.md#7-evaluating-extraction-step-070) would look better than it is. Step 060 warns before paying when it would extract with the model that drafted the ground truth, or one from the same maker.
- **060 on every [record](terminology.md#1-records-and-their-text) (about 36,000 calls): measure before choosing.** Once 20 or more ground truth records are finished, run 060 on them with two or three models, evaluate each with 070, and use the cheapest whose metrics are within the [margin of error](terminology.md#7-evaluating-extraction-step-070) of the best.
- **Decide before the real runs:** every cached answer is tied to its model, so changing models later means paying for those calls again.

## 6. Annotating ground truth (after 050, before 060)

```powershell
py helpers/annotate.py
```

A page opens in your browser: pick the [draft batch](terminology.md#4-ground-truth-and-samples) 050 wrote, correct it, tick *All facts extracted* on each [finished record](terminology.md#4-ground-truth-and-samples), stop with Ctrl+C, commit. How: `annotations/README.md`. It makes no [model calls](terminology.md#8-the-pipeline), so it also works on your personal laptop, if that laptop has run [steps](terminology.md#8-the-pipeline) 010 to 030 and has the draft batch.

## 7. If something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| *Test call to … failed* (040, 050, 060 or 070 stops) | The key or the connection is wrong, or Ask Sage refuses you that [model](terminology.md#8-the-pipeline). Nothing else was called. | If Ask Sage says the model isn't allowed, choose another (`--model`; see *Choosing a model*). Otherwise check `.env`, and that you're on NASA's network (or VPN). |
| *Set ASKSAGE_EMAIL and ASKSAGE_API_KEY* | `.env` is missing or misspelled. | Section 3. |
| *Failed to resolve 'api.asksage.ai.nasa.gov'* | The laptop can't reach Ask Sage. | Connect to NASA's network or VPN. |
| *missing input files* | An earlier [step](terminology.md#8-the-pipeline) hasn't run yet. | Run the steps in order (section 4). |
| *running scripts is disabled* | PowerShell's script policy. | Part 3 of `docs/virtual_environment_setup.md`. |

## 8. Tracing where something came from

Any record, [triple instance](terminology.md#2-triples), [classed triple](terminology.md#2-triples), or [schema entry](terminology.md#3-schemas) can be traced back to the API request that first returned it:

```powershell
py helpers/audit.py <record id>
```

See `helpers/audit.md`.

## Added later

*(New items go here.)*
