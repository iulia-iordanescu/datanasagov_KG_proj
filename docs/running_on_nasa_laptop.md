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
git switch main
git pull
```

The work is on the branch `main`.

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
| 070 evaluate | `py 070_evaluate/run.py` | not yet measured | **yes**: two kinds of call, each only when needed: one call per 100 [component classes](terminology.md#3-schemas) of the [current schema](terminology.md#6-extracting-with-a-schema-step-060) not yet in `annotations/component_class_mapping.csv`, only when there are some (then check those rows and run it again); and, on a run that gets past the [translation table](terminology.md#7-evaluating-extraction-step-070), one call suggesting counterparts for the rows that say `(none)`, only when a row of the current schema says `(none)` while the [ground truth schema](terminology.md#3-schemas) has a component class of the same kind that nothing translates to (cached by the lists asked about, so the same lists are never paid for twice) |

Each step ends by printing where its [report](terminology.md#8-the-pipeline) is (`outputs/reports/<run id>.md`). Read the report's **Warnings** before running the next step. Each step's guide (`<step>/<step>.md`) says what every warning means and what to do.

**Or all in order:** `py run_pipeline.py` runs the steps above one after the other, each exactly as its command would (`--from 040`, `--to 060`, or `--only 070` for part of them). Each step that pays still asks before paying. It stops at the first step that doesn't finish; 050 drafts a new [drafted batch](terminology.md#4-ground-truth-and-samples) only when none is waiting for you to correct; 060 and 070 wait until the ground truth has a [finished record](terminology.md#4-ground-truth-and-samples). At the end it prints where its own report is (`outputs/reports/000_pipeline_<date>_<time>.md`): each step's status, headline numbers, warnings, and report, and what to do next. `py run_pipeline.py --status` shows what to do next at any time, running nothing (each item explained in `docs/upkeep.md`). For the test run (section 5), run the steps one by one: their tiny settings differ from step to step.

**How a step ends.** Each step ends with one of four statuses, given in its report (*Run*, *Status*) and its last line, each with its exit code: `ran` (0: it finished, and wrote its outputs and manifest), `stopped` (2: on purpose, for one of these, all of them: a check found a problem you can fix (each step's guide, *Checks and warnings*, lists its own; rows for you to check among them), a setting below its minimum or one the model calls can't use (`service`, `model`, `thinking`), a key missing from `.env`, the question before paying (or 070's question about its warnings) declined or its input closed, the [test call](terminology.md#8-the-pipeline) failed or was cut off, or the early stop), `interrupted` (130: Ctrl+C, whenever you press it, during the [model calls](terminology.md#8-the-pipeline) and at the question before paying too; every answer already received is kept in the cache), or `failed` (1: an error, a missing input file among them). After any but `ran`, the previous run's manifest is put back only if every output file it lists is unchanged. `run_pipeline.py`'s report gives each step one of these, or one of three more for a step it didn't start: `kept` (050, while a drafted batch waits for you), `skipped` (060 and 070, while the ground truth has no finished record), or `not run` (an earlier step didn't end `ran`, `kept`, or `skipped`). Its own exit code is 0, or the exit code of the first step that ended `stopped`, `interrupted`, or `failed`.

### Settings several steps share

Each step's settings are in its guide (*Settings*) and its [control panel](terminology.md#8-the-pipeline) (`run.py`). Give one on the command line as `--<setting> <value>`, e.g. `--records_per_batch 5` (`--records-per-batch 5` works too). A value the step can't use stops it, before any [paid call](terminology.md#8-the-pipeline), saying so.

| Setting | Steps | Values |
|---|---|---|
| any true/false setting (e.g. `confirm_paid_calls`) | every step that has one | `true`, `yes`, `on`, or `1`; `false`, `no`, `off`, or `0`; in any case. Anything else stops the step (*expected true or false*). |
| `ids` | 050, 060 | Exactly these records. Either the ids themselves, separated by commas or spaces (`--ids "a1,b2"`), or the path of a file: a value ending in `.txt` or `.csv`, or holding a `/` or `\`, is read as a path. In the file, one id per line: only the text before a line's first comma counts (so a CSV whose first column is the id works), quotes around it removed; blank lines, lines starting with `#`, and a line `id` (in any case) are skipped. An id listed twice counts once. A file that isn't there stops the step (*The setting ids names the file …, which doesn't exist*). |
| `service` | 040, 050, 060, 070 | `litellm` (NASA's LiteLLM, https://proxy.fast.luna.nasa.gov, the default) or `asksage` (NASA's Ask Sage). Each has its own key in `.env` (section 3) and its own model names. Anything else stops the step (*The setting service is …*). Every cached answer is tied to its service and model. |
| `model` | 040, 050, 060, 070 | A model's name, as the service names it: `py helpers/models.py --service <service>` lists the models the service shows your account; a listed one may still refuse you, which the run's [test call](terminology.md#8-the-pipeline) finds out for the price of that call. Empty stops the step (*The setting model is empty*). Every cached answer is tied to its model (and service): another model asks everything again, and switching back reuses the earlier answers. Which model where: *Choosing a model* (section 5). |
| `thinking` | 040, 050, 060, 070 | `low` (the default), `medium`, `high`, or `model_default` (nothing sent). Sent only to the models that take it (Gemini 2.5 and later, through LiteLLM); their thinking counts against the longest answer allowed (*The thinking cap*, section 5). Anything else stops the step (*The setting thinking is …*). |

## 5. The steps that cost money: 040, 050, 060, 070

Each sends [texts](terminology.md#1-records-and-their-text) to the AI [model](terminology.md#8-the-pipeline), and each request is a [paid call](terminology.md#8-the-pipeline). Before its first call, each one prints its plan (how many calls, which model) and waits: **Enter** goes ahead, and so do `y` and `yes` (in any case, spaces around them ignored); anything else, or no keyboard attached (a run whose input is closed), stops it (`stopped`), and Ctrl+C interrupts it (`interrupted`), having spent nothing. Every question a step asks before paying takes these answers (070's question about its warnings, and `py helpers/models.py --try`'s, too). If the [run](terminology.md#8-the-pipeline) can't do exactly what you asked, it says so above that question. Its first call is the [test call](terminology.md#8-the-pipeline), a one-line check that your key and the model work, so a mistake costs one call, not hundreds.

Every model answer is kept in the [step](terminology.md#8-the-pipeline)'s `cache/` folder under `outputs/`, so a rerun pays only for what isn't there yet. **Don't delete `outputs/`** unless you mean to pay for those calls again.

**What a saved answer depends on.** Each answer in a step's `cache/` is filed under a fingerprint of exactly these three, and nothing else: (1) the model, as the cache names it: through Ask Sage, the model's name alone (as before a second service existed, so the answers paid for then stay valid); through LiteLLM, the service and the model (`litellm:<model>`), since two services may give one name to different models; (2) the thinking cap, only when one is sent (*The thinking cap*, below); (3) the prompt exactly as sent: the step's prompt file with everything filled into it (the rules and the reply format of `common/common_prompts/`, the schema, the [text piece](terminology.md#1-records-and-their-text), the batch of [component instances](terminology.md#2-triples), …). Change any of them and that answer is asked, and paid for, again; every other answer is reused. So editing a prompt file asks again exactly the calls that use it: the files of `common/common_prompts/` are used by 040, 050, and 060 alike, so editing one asks all three again. Not part of it: the temperature (changing it in `common/common_helpers/llm.py` reuses the old answers), the code that reads the answers, and `MAX_ANSWER_TOKENS`, which counts only for an answer cut off at it (*A cut-off isn't paid for twice*, below). A cache file that can't be read (cut short, or edited by hand) is treated as empty, so its answers are asked again: it is first copied aside as `<stage>.unreadable.json` (then `-2`, `-3`, …), and the run warns, naming both files (code: `common/common_helpers/cache.py`).

### While a step pays: what you see, and the guards

After you press Enter, the step prints:

- **The [test call](terminology.md#8-the-pipeline)'s result**, in one line, e.g. `test call: ok (answer 3 tokens, thinking 120 tokens)`. Tokens are the units the service counts and bills; *thinking* is explained under *The thinking cap* below.
- **Progress**, e.g. `model calls: 3 of 12 done, 0 failed, about 1 min left`: at most one line every 10 seconds, and always for a [stage](terminology.md#8-the-pipeline)'s first and last call, so 2 calls show 2 lines and 36,000 calls don't flood the screen. Until 3 calls have finished it says *estimating the time left…*. The stages that ask one prompt at a time (040's labeling, merging, and defining; 070's translations) show `model calls: N done, 0 failed`. Cut-offs are counted among the failed ones, e.g. `1 failed (1 cut off)`.

The [report](terminology.md#8-the-pipeline)'s *Model calls* section then gives the totals: calls, tokens sent and received, thinking tokens (where the service reports them), failed calls, and cut-offs.

**The thinking cap (the setting `thinking`).** Some models think before they answer: they write reasoning you don't see, billed as answer tokens, and it counts against the longest answer allowed (`MAX_ANSWER_TOKENS` in `common/common_helpers/llm.py`, 16,000 tokens; Google's [Gemini thinking docs](https://ai.google.dev/gemini-api/docs/thinking) say the limit includes the thinking). Thinking that isn't capped can use most of those tokens and leave the answer cut off: on 2026-10-21, `gemini-2.5-pro`'s answer for a 1,503-character [record](terminology.md#1-records-and-their-text) was cut off after 10,623 characters. Each step that pays has the setting `thinking` (its values: section 4, *Settings several steps share*); `model_default` sends nothing, so the model thinks as it does by default. It is sent as LiteLLM's `reasoning_effort`, and only where LiteLLM documents it ([LiteLLM's Gemini page](https://docs.litellm.ai/docs/providers/gemini)): to Gemini 2.5 and later. For Gemini 2.5 Pro, whose thinking can't be turned off, LiteLLM makes `low` a thinking budget of 1,024 tokens, so the answer keeps about 15,000 of the 16,000; for Gemini 3, the thinking level `low`. Claude models think only when asked ([LiteLLM's Anthropic page](https://docs.litellm.ai/docs/providers/anthropic)), so nothing is sent to them; nothing is sent to other models (they might refuse a parameter they don't take), nor through Ask Sage. When the cap is sent, it is part of each cached answer's [fingerprint](terminology.md#8-the-pipeline): changing it asks those calls again. Whether more thinking gives better answers here isn't measured yet; to find out, compare runs (`py helpers/compare_runs.py`).

**The test call's check.** If the test call's one-line answer is cut off, the step stops: every answer would be. If its thinking used half or more of the 16,000 tokens, the step warns, says which setting to change, and asks again before paying for more (with `confirm_paid_calls` false it goes on, and the warning is in the report).

**The early stop.** When 3 of a [run](terminology.md#8-the-pipeline)'s first 10 [model calls](terminology.md#8-the-pipeline) about records' [text pieces](terminology.md#1-records-and-their-text) (040's extraction, 050's drafting, 060's extraction) fail (cut-offs included; `EARLY_STOP_FAILURES` and `EARLY_STOP_WINDOW` in `common/common_helpers/llm.py`), the step stops before paying for more, naming the records, why each failed, and what to change. The calls already under way are waited for, and their answers kept in the cache; the rest aren't made. Failures after the first 10 calls don't stop the run: the records they belong to are left out and listed in the report's warnings. The stages that ask one prompt at a time (040's labeling, merging, and defining; 070's translations) make few calls, and 040's labeling expects some failures (it asks a refused batch again in halves to find the item refused), so the early stop doesn't watch them.

**A cut-off isn't paid for twice.** An answer cut off at the length limit is kept in the cache as cut off: a rerun with the same settings reports the failure again without a call, since asking again would get the same cut. Raising `MAX_ANSWER_TOKENS`, or changing `thinking` for a model it is sent to, asks again.

**The failed-call record**, `outputs/logs/<run id>_failed_calls.jsonl`, beside the run's [log](terminology.md#8-the-pipeline): one line for each model call that failed, was cut off, or wasn't made because of the early stop (`outcome`: `failed`, `cut_off`, or `not_sent`), with when, the step and run, the stage (`stage`: `test call`; 040's `extract`, `label`, `merge`, `define`; 050's `draft`; 060's `extract`; 070's `map_component_classes`, `suggest_component_classes`) and, for a call about a record's text, the record and text piece (`record`, `text_piece`, counted from 1), the model and every setting the call was sent with (`thinking` among them, and each setting as the request sent it), the prompt's fingerprint and size and the request's size, the service's finish reason (and the model maker's own, when the service passes it on), its token counts (prompt, answer, thinking) and its whole usage, the HTTP status and the service's error message, the error and its type, how many attempts were made and how long they took, the answer received (a cut-off one whole), and what to change. It is written only when something fails; the report's *Run* table and the run's last lines name it. It never holds a key. It's in `outputs/`, so it isn't in Git: to get help with a failure, share this file.

### Test run first

The cheapest way to check that everything works, about 20 [paid calls](terminology.md#8-the-pipeline) in all:

1. **010, 020, 030: run them for real** (section 4). They cost nothing. A "quick trial" [harvest](terminology.md#1-records-and-their-text) (`--max_records`) only checks that harvesting works: 030 writes its file only once, so it won't split a trial catalog. Run the full harvest before 020 and 030.
2. **040–070: tiny runs**, in order:

   | [Step](terminology.md#8-the-pipeline) | Command | Paid calls, roughly |
   |---|---|---|
   | 040 | `py 040_induce_schema/run.py --induction_maintainers 2 --texts_per_maintainer 2` | 10–15 (4 [texts](terminology.md#1-records-and-their-text), then labeling, merging, defining) |
   | 050 | `py 050_annotate/run.py --records_per_batch 1` | 2 (one [record](terminology.md#1-records-and-their-text), and the [test call](terminology.md#8-the-pipeline)) |
   | 060 | `py 060_extract/run.py` | 3 (the finished [ground truth](terminology.md#4-ground-truth-and-samples) records, 2 as of 2026-10-01, and the test call) |
   | 070 | `py 070_evaluate/run.py` | 2 the first time ([component class](terminology.md#3-schemas) translations, and the test call); it then stops so you can check the rows it added to `annotations/component_class_mapping.csv`. Run it again: 0 calls, or 2 (the test call, and the suggestion call: a row says `(none)` while the [ground truth schema](terminology.md#3-schemas) has a component class of the same kind that nothing translates to). |

3. **Check you're charged properly.** For each [run](terminology.md#8-the-pipeline), compare the plan it prints before you press Enter ("… will make N [model call](terminology.md#8-the-pipeline)(s) …") with its [report](terminology.md#8-the-pipeline)'s *Model calls* table (`outputs/reports/<run id>.md`): calls per [stage](terminology.md#8-the-pipeline), the test call, and the total paid. Running the same command again should show 0 paid calls: the cache works, and nothing is paid twice.

Nothing is wasted: the real 040 run reuses the tiny run's saved answers; 050's record is real work (correct it in `py helpers/annotate.py`); 060 and 070 simply run again after the real 040.

### Choosing a model

Each of 040–070 has a `service` [setting](terminology.md#8-the-pipeline), the service that reaches the model (its values: section 4, *Settings several steps share*). Each service names its [models](terminology.md#8-the-pipeline) its own way (Ask Sage's `google-claude-sonnet-5` is LiteLLM's `claude-sonnet-5`), and each step has a `model` setting: by default `claude-opus-5.5` for 040, 060, and 070, and `gemini-2.5-pro` for 050 (LiteLLM names). On 2026-10-12, LiteLLM let this project's key use both, and `gemini-3.1-pro-preview`; Ask Sage refused Opus. LiteLLM's `gpt-5.5` refused the pipeline's temperature 0 (it accepts only 1), so GPT-5 models can't be used as the code stands. To see which models a service lists for your account (free; LiteLLM's list shows only the models your key may use; add `--service asksage` for Ask Sage's):

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

### Shared warnings and stops

Each step's guide, under *Checks and warnings*, lists that step's own messages. This table lists the ones several steps share, and how the laptop or a service can fail. The ones starting *Ground truth,* are the [ground truth](terminology.md#4-ground-truth-and-samples)'s own problems, all six of them (their one list): every step that reads it (040, 050, 060, 070) shows them in its report's warnings; 050 and 060 also before paying, and 070 before evaluating, asking whether to go ahead; 040 reads the ground truth only after its [model calls](terminology.md#8-the-pipeline) (to compare its schema with the [ground truth schema](terminology.md#3-schemas)), so it shows them in its report only.

| What you see | What it means | What to do |
|---|---|---|
| *The setting model is empty, so no model can be called* (040, 050, 060, or 070 stops) | The `model` setting is empty. | Give a model's name (`py helpers/models.py` lists them). |
| *The setting service is …, which isn't a service the pipeline can reach* | The `service` setting is none of its values (section 4, *Settings several steps share*). | Give one of them with `--service`. |
| *Test call to … failed* (040, 050, 060, or 070 stops) | The key or the connection is wrong, or the service refuses you that [model](terminology.md#8-the-pipeline), or a setting sent with it. Nothing else was called. | If the service says the model isn't allowed, choose another (`--model`; see *Choosing a model*). If its message names `reasoning_effort`, give `--thinking model_default`, which sends no thinking cap. Otherwise check `.env`, and that you're on NASA's network (or VPN). `py helpers/models.py --service <service> --try <name> ...` tells which models you may use. |
| *Test call to … was cut off at the longest length allowed … on a one-line answer* (the step stops) | The [test call](terminology.md#8-the-pipeline)'s answer reached `MAX_ANSWER_TOKENS`, so every answer would. Nothing else was called. | Do what the message says: usually `--thinking low` (section 5, *The thinking cap*). |
| *The test call's one-line answer used N tokens thinking, …% of the 16,000 tokens each answer may use* (asked before paying for more; also in the report's warnings) | The model's thinking leaves a [record](terminology.md#1-records-and-their-text)'s answer little room, so answers are likely to be cut off. | Cancel, and do what the message says: at `medium` or `high`, a lower `thinking`; at `model_default`, for a model the cap is sent to, `--thinking low`; at `low` (the default), or for a model the cap isn't sent to, raise `MAX_ANSWER_TOKENS` (at `low`, with `--thinking model_default` as an option once it is higher), or another model. Or go ahead, and let the early stop catch it. |
| *The setting thinking is …, which isn't a level the pipeline knows* | The `thinking` setting is none of its values (section 4, *Settings several steps share*). | Give one of them with `--thinking`. |
| *Step NNN stopped early: N of the first M model calls of this run failed (…)* | The early stop (section 5): too many of the run's first calls failed, so the step stopped before paying for the rest. Answers already received are kept in the cache. | Do what the message says, from the failures it lists; the failed-call record (`outputs/logs/<run id>_failed_calls.jsonl`) has each call's details. Then run the step again: it pays only for the rest. |
| *LITELLM_API_KEY isn't set, so no model can be called through LiteLLM* | LiteLLM's key isn't in `.env` (with `service` `litellm`, the default), or its name is misspelled. | Section 3. |
| *ASKSAGE_EMAIL and ASKSAGE_API_KEY aren't set, so no model can be called* (or one of them isn't) | With `--service asksage`: the Ask Sage email and key aren't in `.env`, or a name is misspelled. | Section 3. |
| *Cancelled. Nothing was spent.* (or *Cancelled. Only the test call was paid for.*, at the second question, after the test call) | You declined at the question before paying (the step ends `stopped`). | Nothing. |
| *Cancelled with Ctrl+C. Nothing was spent.* (or *… Only the test call was paid for.*) | You pressed Ctrl+C at the question before paying (the step ends `interrupted`). | Nothing. |
| *Stopped with Ctrl+C. Model calls not yet started were cancelled, so they cost nothing.* | You pressed Ctrl+C while the model calls ran (the step ends `interrupted`). | Run the step again: the answers already received are kept in the cache and reused, not paid for again. |
| *Failed to resolve 'api.asksage.ai.nasa.gov'* | The laptop can't reach Ask Sage. | Connect to NASA's network or VPN. |
| *… failed for <id> piece 1: the answer was cut off at the longest length allowed* | The model's answer for that text reached `MAX_ANSWER_TOKENS` (`common/common_helpers/llm.py`, 16,000 tokens) and was cut off. The tokens include the model's thinking: when the service reports it, the message ends *the model spent N of those tokens thinking* (on 2026-10-21, a 1,503-character record's answer was cut off after only 10,623 characters because of thinking: 12,615 of its 15,996 answer tokens (79%) went to Gemini's thinking; on 2026-10-12, an answer of 26,399 characters listing 164 distinct [triple instances](terminology.md#2-triples), with no tokens spent thinking, was cut off by its length alone: `docs/findings.md`). Only that text is left out. The whole answer and the token counts are in the failed-call record (section 5) and in the step's log (a DEBUG line starting "cut-off answer"), so you can see whether the answer was long, repeated itself, or was mostly thinking. A rerun with the same settings doesn't ask it again (*… so not asked again*): it would get the same cut. On Ask Sage no limit can be sent, so a cut answer shows as *isn't a JSON object* instead. | Change the setting the report's warning names. The advice follows the token counts the service reported, not the settings: when thinking took half or more of the tokens, a lower `thinking` for a model the cap is sent to (when it is already `low`, raise `MAX_ANSWER_TOKENS`, with `--thinking model_default` as an option once it is higher), or another model; when the thinking took less and the answer itself is long, raise `MAX_ANSWER_TOKENS`, or, for a long [text piece](terminology.md#1-records-and-their-text), lower the step's `max_chars`; when the service doesn't report thinking tokens, the advice says it can't tell which, and gives both. Lowering `max_chars` doesn't help a short record: it is already one text piece. |
| *… failed for <id> piece 1: no answer within 600 s* | The model took longer than `READ_TIMEOUT` (`common/common_helpers/llm.py`). It isn't asked again in this run, since the service may still be writing, and billing, the first answer. | Run the step again later; if it keeps happening, lower the step's `max_chars`. |
| *… the model gave no usable answer (finish_reason …)* | The model answered nothing usable, e.g. its service's content filter withheld the answer (`content_filter`). Asking again gets the same. | Look at the record's text; if it happens often with one model, try another (`--model`). |
| *Model call … failed (HTTP 429 …); trying again in N s* | The service's rate limit. The step waits as long as the service asks (plus up to 2 s), up to 3 times. | Nothing, unless it fails in the end: then lower the step's `workers` and run it again. |
| *The model's answer to a batch of N was refused (…); asking for each half separately* | 040's labeling or defining hit an item the service won't answer about (e.g. its content filter). The step asks again in halves to find it, and goes on. | Nothing; the report then lists the item(s) refused (`040_induce_schema/040_induce_schema.md`, *Checks and warnings*). |
| *missing input files, so the step can't run:*, then one line per missing file: *<input>: <path> (run `py <step>/run.py` first, or give another file with --<input>)*, or, for a file kept in Git, *<input>: <path> (give the file with --<input>)* | An earlier [step](terminology.md#8-the-pipeline) hasn't run yet, or a file kept in Git isn't there. | Run the steps in order (section 4), or give the file with `--<input>`. |
| *Input `<input>` (<path>) has no readable manifest, so the run that produced it is not recorded* (in the report's warnings) | The input's folder has no `_manifest.json` (or one that can't be read), so which run made it isn't known. | Nothing, if you know where it came from; otherwise run the step that makes it again, which writes a new one. |
| *The setting <setting> must be at least N, but is M, so the step can't run* | A setting below its minimum; each step's guide lists its own minimums. | Give `--<setting>` N or more. |
| *… --<setting>…: expected true or false, got '…'* (the step doesn't start) | A true/false setting given another value (section 4, *Settings several steps share*). | Give one of the values listed there. |
| *The setting ids names the file …, which doesn't exist* (050, 060) | `ids` looks like a path (section 4, *Settings several steps share*), but there's no such file. | Give the file's path from the repository folder, or the ids themselves. |
| *…/records.jsonl line N: id … appears twice, so the step can't tell which record is right* (any step that reads 020's records) | 020 writes each record once: the file was edited, or isn't 020's output. | Run `py 020_clean/run.py` again, then the step. |
| *N answer(s) saved in …/cache/….json were JSON of the wrong shape …, so they were ignored and the model was asked again* (in the report's warnings) | A saved answer that a step can't use, e.g. from an older version of the step: it is never kept as an answer. | Nothing: the new answers replace them. |
| *The model's reply isn't a JSON object (…); asking once more* / *The model's reply is a JSON object of the wrong shape (…); asking once more* (in the log) | An answer the step can't read; it asks once more, saying what was wrong. | Nothing. |
| *… the model's answer isn't a valid JSON object / a JSON object of the shape asked for, N times (…)* | Every try gave such an answer, so that call failed; each answer is in the run's log, on a DEBUG line starting "unusable answer". | Run the step again; if it keeps happening with one model, try another (`--model`). |
| *LiteLLM's reply has no answer in it: …* / *API status N: …* (Ask Sage) | The service answered, but with no model answer in it (or, Ask Sage, with an error status). | Run the step again; if it persists, the service's message says why. |
| *The previous run's output files couldn't be kept in previous_runs/ (…)* / *Tidying previous_runs/ after the run failed (…)* (in the log) | Keeping the earlier version of the output files failed, e.g. a full disk; the run goes on. | The message says: copy the output folder aside if those files matter, and check the disk has space; tidying needs nothing. |
| *Ground truth, record … is in batch_… and batch_…: annotated twice* | A record is annotated twice. It's left out of the ground truth until fixed. | Keep it in one file. |
| *Ground truth, record … (batch_…): all_facts_extracted is 0 on some rows, 1 on others* | Mixed, so the record doesn't count as finished. | Set it the same on every row (the tool's box does). |
| *Ground truth, record … (batch_…): all_facts_extracted is '…' on N row(s), which is neither 0 nor 1* | A hand edit: the column takes only `0` (not finished) and `1` (finished), so the record counts as not finished. | Tick (or untick) *All facts extracted* on the record in the [annotation tool](terminology.md#4-ground-truth-and-samples): saving sets every row to 1 or 0. |
| *Ground truth, record … (batch_…): lines … and … are the same classed triple.*, then each line | [The same classed triple twice](terminology.md#4-ground-truth-and-samples) in one record (a hand edit). Only one copy can be paired, so evaluation would count the other as ground truth only. Step 070 stops until one is deleted. | Delete one of the two rows. |
| *Ground truth, record … (batch_…): lines … and … state the same subject instance, predicate, and object instance, with different entity classes.*, then each line | Likely one fact given two [entity classes](terminology.md#3-schemas) by mistake. | If they state one fact, delete the line with the wrong entity classes. |
| *Ground truth, batch_… lacks the column(s) …; not read* | A ground truth file without one of the columns (see `annotations/README.md`). | Add the column. |
| *running scripts is disabled* | PowerShell's script policy. | Part 3 of `docs/virtual_environment_setup.md`. |

## 8. Tracing where something came from

Any record, [triple instance](terminology.md#2-triples), [classed triple](terminology.md#2-triples), or [schema entry](terminology.md#3-schemas) can be traced back to the API request that first returned it:

```powershell
py helpers/audit.py <record id>
```

See `helpers/audit.md`.

## Added later

*(New items go here.)*
