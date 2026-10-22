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

### While a step pays: what you see, and the guards

After you press Enter, the step prints:

- **The [test call](terminology.md#8-the-pipeline)'s result**, in one line, e.g. `test call: ok (answer 3 tokens, thinking 120 tokens)`. Tokens are the units the service counts and bills; *thinking* is explained under *The thinking cap* below.
- **Progress**, e.g. `model calls: 3 of 12 done, 0 failed, about 1 min left`: at most one line every 10 seconds, and always for a [stage](terminology.md#8-the-pipeline)'s first and last call, so 2 calls show 2 lines and 36,000 calls don't flood the screen. Until 3 calls have finished it says *estimating the time left…*. The stages that ask one prompt at a time (040's labeling, merging, and defining; 070's translations) show `model calls: N done, 0 failed`. Cut-offs are counted among the failed ones, e.g. `1 failed (1 cut off)`.

The [report](terminology.md#8-the-pipeline)'s *Model calls* section then gives the totals: calls, tokens sent and received, thinking tokens (where the service reports them), failed calls, and cut-offs.

**The thinking cap (the setting `thinking`).** Some models think before they answer: they write reasoning you don't see, billed as answer tokens, and it counts against the longest answer allowed (`MAX_ANSWER_TOKENS` in `common/common_helpers/llm.py`, 16,000 tokens; Google's [Gemini thinking docs](https://ai.google.dev/gemini-api/docs/thinking) say the limit includes the thinking). Thinking that isn't capped can use most of those tokens and leave the answer cut off: on 2026-10-21, `gemini-2.5-pro`'s answer for a 1,503-character [record](terminology.md#1-records-and-their-text) was cut off after 10,623 characters. Each step that pays has the setting `thinking`: `low` (the default), `medium`, `high`, or `model_default` (nothing sent: the model thinks as it does by default). It is sent as LiteLLM's `reasoning_effort`, and only where LiteLLM documents it ([LiteLLM's Gemini page](https://docs.litellm.ai/docs/providers/gemini)): to Gemini 2.5 and later. For Gemini 2.5 Pro, whose thinking can't be turned off, LiteLLM makes `low` a thinking budget of 1,024 tokens, so the answer keeps about 15,000 of the 16,000; for Gemini 3, the thinking level `low`. Claude models think only when asked ([LiteLLM's Anthropic page](https://docs.litellm.ai/docs/providers/anthropic)), so nothing is sent to them; nothing is sent to other models (they might refuse a parameter they don't take), nor through Ask Sage. When the cap is sent, it is part of each cached answer's [fingerprint](terminology.md#8-the-pipeline): changing it asks those calls again. Whether more thinking gives better answers here isn't measured yet; to find out, compare runs (`py helpers/compare_runs.py`).

**The test call's check.** If the test call's one-line answer is cut off, the step stops: every answer would be. If its thinking used half or more of the 16,000 tokens, the step warns, says which setting to change, and asks again before paying for more (with `confirm_paid_calls` false it goes on, and the warning is in the report).

**The early stop.** When 3 of a [run](terminology.md#8-the-pipeline)'s first 10 [model calls](terminology.md#8-the-pipeline) about records' [text pieces](terminology.md#1-records-and-their-text) (040's extraction, 050's drafting, 060's extraction) fail (cut-offs included; `EARLY_STOP_FAILURES` and `EARLY_STOP_WINDOW` in `common/common_helpers/llm.py`), the step stops before paying for more, naming the records, why each failed, and what to change. The calls already under way are waited for, and their answers kept in the cache; the rest aren't made. Failures after the first 10 calls don't stop the run: the records they belong to are left out and listed in the report's warnings. The stages that ask one prompt at a time (040's labeling, merging, and defining; 070's translations) make few calls, and 040's labeling expects some failures (it asks a refused batch again in halves to find the item refused), so the early stop doesn't watch them.

**A cut-off isn't paid for twice.** An answer cut off at the length limit is kept in the cache as cut off: a rerun with the same settings reports the failure again without a call, since asking again would get the same cut. Raising `MAX_ANSWER_TOKENS`, or changing `thinking` for a model it is sent to, asks again.

**The failed-call record**, `outputs/logs/<run id>_failed_calls.jsonl`, beside the run's [log](terminology.md#8-the-pipeline): one line for each model call that failed, was cut off, or wasn't made because of the early stop, with when, the step and run, the record and text piece (or the stage), the model and every setting the call was sent with (`thinking` among them, and each setting as the request sent it), the prompt's fingerprint and size and the request's size, the service's finish reason (and the model maker's own, when the service passes it on), its token counts (prompt, answer, thinking) and its whole usage, the HTTP status and the service's error message, the error and its type, how many attempts were made and how long they took, the answer received (a cut-off one whole), and what to change. It is written only when something fails; the report's *Run* table and the run's last lines name it. It never holds a key. It's in `outputs/`, so it isn't in Git: to get help with a failure, share this file.

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
| *Test call to … failed* (040, 050, 060, or 070 stops) | The key or the connection is wrong, or the service refuses you that [model](terminology.md#8-the-pipeline), or a setting sent with it. Nothing else was called. | If the service says the model isn't allowed, choose another (`--model`; see *Choosing a model*). If its message names `reasoning_effort`, give `--thinking model_default`, which sends no thinking cap. Otherwise check `.env`, and that you're on NASA's network (or VPN). `py helpers/models.py --service <service> --try <name> ...` tells which models you may use. |
| *Test call to … was cut off at the longest length allowed … on a one-line answer* (the step stops) | The [test call](terminology.md#8-the-pipeline)'s answer reached `MAX_ANSWER_TOKENS`, so every answer would. Nothing else was called. | Do what the message says: usually `--thinking low` (section 5, *The thinking cap*). |
| *The test call's one-line answer used N tokens thinking, …% of the 16,000 tokens each answer may use* (asked before paying for more; also in the report's warnings) | The model's thinking leaves a [record](terminology.md#1-records-and-their-text)'s answer little room, so answers are likely to be cut off. | Cancel, and do what the message says: at `medium` or `high`, a lower `thinking`; at `model_default`, for a model the cap is sent to, `--thinking low`; at `low` (the default), or for a model the cap isn't sent to, raise `MAX_ANSWER_TOKENS` (at `low`, with `--thinking model_default` as an option once it is higher), or another model. Or go ahead, and let the early stop catch it. |
| *The setting thinking is …, which isn't a level the pipeline knows* | The `thinking` setting is none of `low`, `medium`, `high`, `model_default`. | Give one of them with `--thinking`. |
| *Step NNN stopped early: N of the first M model calls of this run failed (…)* | The early stop (section 5): too many of the run's first calls failed, so the step stopped before paying for the rest. Answers already received are kept in the cache. | Do what the message says, from the failures it lists; the failed-call record (`outputs/logs/<run id>_failed_calls.jsonl`) has each call's details. Then run the step again: it pays only for the rest. |
| *LITELLM_API_KEY isn't set, so no model can be called through LiteLLM* | LiteLLM's key isn't in `.env` (with `service` `litellm`, the default), or its name is misspelled. | Section 3. |
| *ASKSAGE_EMAIL and ASKSAGE_API_KEY aren't set, so no model can be called* (or one of them isn't) | With `--service asksage`: the Ask Sage email and key aren't in `.env`, or a name is misspelled. | Section 3. |
| *Cancelled. Nothing was spent.* | You declined at the question before paying. | Nothing. |
| *Stopped with Ctrl+C. Model calls not yet started were cancelled, so they cost nothing.* | You pressed Ctrl+C while the [model calls](terminology.md#8-the-pipeline) ran. | Run the step again: the answers already received are kept in the cache and reused, not paid for again. |
| *Failed to resolve 'api.asksage.ai.nasa.gov'* | The laptop can't reach Ask Sage. | Connect to NASA's network or VPN. |
| *… failed for <id> piece 1: the answer was cut off at the longest length allowed* | The model's answer for that text reached `MAX_ANSWER_TOKENS` (`common/common_helpers/llm.py`, 16,000 tokens) and was cut off. The tokens include the model's thinking: when the service reports it, the message ends *the model spent N of those tokens thinking* (on 2026-10-21, a 1,503-character record's answer was cut off after only 10,623 characters because of thinking: 12,615 of its 15,996 answer tokens (79%) went to Gemini's thinking; on 2026-10-12, an answer of 26,399 characters listing 164 distinct [triple instances](terminology.md#2-triples), with no tokens spent thinking, was cut off by its length alone: `docs/findings.md`). Only that text is left out. The whole answer and the token counts are in the failed-call record (section 5) and in the step's log (a DEBUG line starting "cut-off answer"), so you can see whether the answer was long, repeated itself, or was mostly thinking. A rerun with the same settings doesn't ask it again (*… so not asked again*): it would get the same cut. On Ask Sage no limit can be sent, so a cut answer shows as *isn't a JSON object* instead. | Change the setting the report's warning names. The advice follows the token counts the service reported, not the settings: when thinking took half or more of the tokens, a lower `thinking` for a model the cap is sent to (when it is already `low`, raise `MAX_ANSWER_TOKENS`, with `--thinking model_default` as an option once it is higher), or another model; when the thinking took less and the answer itself is long, raise `MAX_ANSWER_TOKENS`, or, for a long [text piece](terminology.md#1-records-and-their-text), lower the step's `max_chars`; when the service doesn't report thinking tokens, the advice says it can't tell which, and gives both. Lowering `max_chars` doesn't help a short record: it is already one text piece. |
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
