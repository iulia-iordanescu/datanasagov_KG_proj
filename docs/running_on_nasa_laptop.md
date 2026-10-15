# Running the pipeline on the NASA laptop

The code is built and tested on a personal laptop, which can't reach NASA's LiteLLM or Ask Sage, the NASA services that reach the AI [model](terminology.md#8-the-pipeline). Real [runs](terminology.md#8-the-pipeline) happen on the NASA laptop, after pulling the code from GitHub. This page is the checklist for that. Items get added at the end as the pipeline grows.

Two things never travel through Git, on purpose:

- **`.env`**, which holds your service keys: a key in Git could be read by anyone who can see the repository.
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

## 3. Add your keys

Create the file `.env` with your service keys: part 6 of `docs/virtual_environment_setup.md`. NASA's LiteLLM (the default `service`, see *Choosing a model*) needs the line `LITELLM_API_KEY=sk-...`; Ask Sage needs your email and key. A LiteLLM key is made in LiteLLM's dashboard (https://proxy.fast.luna.nasa.gov/ui/, *Virtual Keys*, *Create New Key*; key type *AI APIs*; models left empty for all your team's models). LiteLLM shows the full key once: copy it into `.env` at once, and never into a chat or a file Git tracks.

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
| 070 evaluate | `py 070_evaluate/run.py` | not yet measured | **yes** (one call per 100 [component classes](terminology.md#3-schemas) of the [current schema](terminology.md#6-extracting-with-a-schema-step-060) not yet in `annotations/component_class_mapping.csv`, only when there are some; then check those rows and run it again) |

Each step ends by printing where its [report](terminology.md#8-the-pipeline) is (`outputs/reports/<run id>.md`). Read the report's **Warnings** before running the next step. Each step's guide (`<step>/<step>.md`) says what every warning means and what to do.

**Or all in order:** `py run_pipeline.py` runs the steps above one after the other, each exactly as its command would (`--from 040`, `--to 060`, or `--only 070` for part of them). Each step that pays still asks before paying. It stops at the first step that doesn't finish; 050 drafts a new [drafted batch](terminology.md#4-ground-truth-and-samples) only when none is waiting for you to correct; 060 and 070 wait until the ground truth has a [finished record](terminology.md#4-ground-truth-and-samples). At the end it prints where its own report is (`outputs/reports/000_pipeline_<date>_<time>.md`): each step's status, headline numbers, warnings, and report, and what to do next. `py run_pipeline.py --status` shows what to do next at any time, running nothing (each item explained in `docs/upkeep.md`). For the test run (section 5), run the steps one by one: their tiny settings differ from step to step.

## 5. The steps that cost money: 040, 050, 060, 070

Each sends [texts](terminology.md#1-records-and-their-text) to the AI [model](terminology.md#8-the-pipeline), and each request is a [paid call](terminology.md#8-the-pipeline). Before its first call, each one prints its plan (how many calls, which model) and waits: **Enter** goes ahead, anything else stops, having spent nothing. If the [run](terminology.md#8-the-pipeline) can't do exactly what you asked, it says so above that question. Its first call is the [test call](terminology.md#8-the-pipeline), a one-line check that your key and the model work, so a mistake costs one call, not hundreds.

Every model answer is kept in the [step](terminology.md#8-the-pipeline)'s `cache/` folder under `outputs/`, so a rerun pays only for what isn't there yet. **Don't delete `outputs/`** unless you mean to pay for those calls again.

### Test run first

The cheapest way to check that everything works, about 20 [paid calls](terminology.md#8-the-pipeline) in all:

1. **010, 020, 030: run them for real** (section 4). They cost nothing. A "quick trial" [harvest](terminology.md#1-records-and-their-text) (`--max_records`) only checks that harvesting works: 030 writes its file only once, so it won't split a trial catalog. Run the full harvest before 020 and 030.
2. **040–070: tiny runs**, in order:

   | [Step](terminology.md#8-the-pipeline) | Command | Paid calls, roughly |
   |---|---|---|
   | 040 | `py 040_induce_schema/run.py --induction_maintainers 2 --texts_per_maintainer 2` | 10–15 (4 [texts](terminology.md#1-records-and-their-text), then labeling, merging, defining) |
   | 050 | `py 050_annotate/run.py --records_per_batch 1` | 2 (one [record](terminology.md#1-records-and-their-text), and the [test call](terminology.md#8-the-pipeline)) |
   | 060 | `py 060_extract/run.py` | 3 (the finished [ground truth](terminology.md#4-ground-truth-and-samples) records, 2 as of 2026-10-01, and the test call) |
   | 070 | `py 070_evaluate/run.py` | 2 the first time ([component class](terminology.md#3-schemas) translations, and the test call); it then stops so you can check the rows it added to `annotations/component_class_mapping.csv`. Run it again: 0 calls. |

3. **Check you're charged properly.** For each [run](terminology.md#8-the-pipeline), compare the plan it prints before you press Enter ("… will make N [model call](terminology.md#8-the-pipeline)(s) …") with its [report](terminology.md#8-the-pipeline)'s *Model calls* table (`outputs/reports/<run id>.md`): calls per [stage](terminology.md#8-the-pipeline), the test call, and the total paid. Running the same command again should show 0 paid calls: the cache works, and nothing is paid twice.

Nothing is wasted: the real 040 run reuses the tiny run's saved answers; 050's record is real work (correct it in `py helpers/annotate.py`); 060 and 070 simply run again after the real 040.

### Choosing a model

Each of 040–070 has a `service` [setting](terminology.md#8-the-pipeline), the service that reaches the model: `litellm` (NASA's LiteLLM, https://proxy.fast.luna.nasa.gov, the default) or `asksage` (NASA's Ask Sage). Each service names its [models](terminology.md#8-the-pipeline) its own way (Ask Sage's `google-claude-sonnet-5` is LiteLLM's `claude-sonnet-5`), and each step has a `model` setting: by default `claude-opus-5.5` for 040, 060, and 070, and `gemini-2.5-pro` for 050 (LiteLLM names). On 2026-10-12, LiteLLM let this project's key use both, and `gemini-3.1-pro-preview`; Ask Sage refused Opus. LiteLLM's `gpt-5.5` refused the pipeline's temperature 0 (it accepts only 1), so GPT-5 models can't be used as the code stands. To see which models a service lists for your account (free; LiteLLM's list shows only the models your key may use; add `--service asksage` for Ask Sage's):

```powershell
py helpers/models.py
```

A listed model may still refuse you: Ask Sage's list shows what it offers, not what your account is approved for, and a model LiteLLM lists may still fail on a setting it doesn't accept. To find out, try the models you're considering, e.g. `py helpers/models.py --try claude-sonnet-5 <name> <name>`, with names copied from the list, or `--try all` for every listed one. Each try is the one-line [test call](terminology.md#8-the-pipeline) a [step](terminology.md#8-the-pipeline) makes first: one tiny [paid call](terminology.md#8-the-pipeline) per model, asked about before paying. It prints each model as usable, or refused with the service's reason (e.g. Ask Sage's `model_not_permitted`).

Which model where:

- **040, 050, 070: the strongest model that answers you.** Their calls are few (tens to a few hundred), and their quality matters most: 040 shapes the induced [schema](terminology.md#3-schemas), 050 decides how much you correct by hand, 070's translations decide the metrics.
- **050 and 060: two different models, from different makers if you can** (e.g. a Claude model for one, a Gemini or GPT model for the other). The [ground truth](terminology.md#4-ground-truth-and-samples) starts as 050's [drafted triples](terminology.md#4-ground-truth-and-samples); if 060 used the same model, the [facts](terminology.md#2-triples) that model misses would be missing from both, and [recall](terminology.md#7-evaluating-extraction-step-070) would look better than it is. Step 060 warns before paying when it would extract with the model that drafted the ground truth, or one from the same maker.
- **060 on every [record](terminology.md#1-records-and-their-text) (about 36,000 calls): measure before choosing.** Once 20 or more [tuning records](terminology.md#7-evaluating-extraction-step-070) are finished, run 060 on them with two or three models, evaluate each with 070, compare them (`py helpers/compare_runs.py`, `helpers/compare_runs.md`), and use the cheapest that the comparison can't tell apart from the best.
- **Decide before the real runs:** every cached answer is tied to its model, so changing models later means paying for those calls again.

## 6. Annotating ground truth (after 050, before 060)

```powershell
py helpers/annotate.py
```

The tool's home page opens in your browser: in **[Ground truth](terminology.md#4-ground-truth-and-samples)**, pick the [drafted batch](terminology.md#4-ground-truth-and-samples) 050 wrote, correct it, tick *All facts extracted* on each [finished record](terminology.md#4-ground-truth-and-samples), stop with Ctrl+C, commit. How: `annotations/README.md`. What to do while annotating, and when: `docs/upkeep.md`; the home page lists what is waiting. It makes no [model calls](terminology.md#8-the-pipeline), so it also works on your personal laptop, if that laptop has run [steps](terminology.md#8-the-pipeline) 010 to 030 and has the drafted batch.

## 7. If something goes wrong

| What you see | What it means | What to do |
|---|---|---|
| *The setting model is empty, so no model can be called* (040, 050, 060, or 070 stops) | The `model` setting is empty. | Give a model's name (`py helpers/models.py` lists them). |
| *The setting service is …, which isn't a service the pipeline can reach* | The `service` setting is neither `litellm` nor `asksage`. | Give `--service litellm` or `--service asksage`. |
| *Test call to … failed* (040, 050, 060, or 070 stops) | The key or the connection is wrong, or the service refuses you that [model](terminology.md#8-the-pipeline). Nothing else was called. | If the service says the model isn't allowed, choose another (`--model`; see *Choosing a model*). Otherwise check `.env`, and that you're on NASA's network (or VPN). `py helpers/models.py --service <service> --try <name> ...` tells which models you may use. |
| *LITELLM_API_KEY isn't set, so no model can be called through LiteLLM* | LiteLLM's key isn't in `.env` (with `service` `litellm`, the default), or its name is misspelled. | Section 3. |
| *ASKSAGE_EMAIL and ASKSAGE_API_KEY aren't set, so no model can be called* (or one of them isn't) | With `--service asksage`: the Ask Sage email and key aren't in `.env`, or a name is misspelled. | Section 3. |
| *Cancelled. Nothing was spent.* | You declined at the question before paying. | Nothing. |
| *Stopped with Ctrl+C. Model calls not yet started were cancelled, so they cost nothing.* | You pressed Ctrl+C while the [model calls](terminology.md#8-the-pipeline) ran. | Run the step again: the answers already received are kept in the cache and reused, not paid for again. |
| *Failed to resolve 'api.asksage.ai.nasa.gov'* | The laptop can't reach Ask Sage. | Connect to NASA's network or VPN. |
| *… failed for <id> piece 1: the answer was cut off at the longest length allowed* | The model's answer for that text reached `MAX_ANSWER_TOKENS` (`common/common_helpers/llm.py`, 16,000 tokens; one answer was cut off at 25,658 characters on 2026-10-12) and was cut off. Only that text is left out. The whole answer is in the step's log (`outputs/logs/<run id>.log`, a DEBUG line starting "cut-off answer", with the service's token counts), so you can see whether it was long or repeated itself. Asking again with the same settings gets the same cut. On Ask Sage no limit can be sent, so a cut answer shows as *isn't a JSON object* instead. | If it happens often, raise `MAX_ANSWER_TOKENS`, or lower the step's `max_chars` so each [text piece](terminology.md#1-records-and-their-text), and so each answer, is shorter. |
| *… failed for <id> piece 1: no answer within 600 s* | The model took longer than `READ_TIMEOUT` (`common/common_helpers/llm.py`). It isn't asked again in this run, since the service may still be writing, and billing, the first answer. | Run the step again later; if it keeps happening, lower the step's `max_chars`. |
| *… the model gave no usable answer (finish_reason …)* | The model answered nothing usable, e.g. its service's content filter withheld the answer (`content_filter`). Asking again gets the same. | Look at the record's text; if it happens often with one model, try another (`--model`). |
| *Model call … failed (HTTP 429 …); trying again in N s* | The service's rate limit. The step waits as long as the service asks (plus up to 2 s), up to 3 times. | Nothing, unless it fails in the end: then lower the step's `workers` and run it again. |
| *The model's answer to a batch of N was refused (…); asking for each half separately* | 040's labeling or defining hit an item the service won't answer about (e.g. its content filter). The step asks again in halves to find it, and goes on. | Nothing; the report then lists the item(s) refused (`040_induce_schema/040_induce_schema.md`, *Checks and warnings*). |
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
