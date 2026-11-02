# Findings

What has been measured about the pipeline, newest first. Each entry says what was measured, on which runs and data, the numbers, and what they mean and don't mean. How each step works is in its guide; this file holds results. Terms: [docs/terminology.md](terminology.md).

The runs' own files (reports, logs, outputs) stay on the laptop that ran them, in `outputs/`, which Git doesn't carry; each entry names them.

**How this file is kept.** Two parts for two readers. *Current picture* (below) is for reading: what is known now, in plain words, a few lines, rewritten whenever results change, each line linking to the evidence. The dated entries after it are the evidence: what was run, the numbers, and what each result does and doesn't show; they are what later decisions rest on. Entries are never rewritten: a later measurement that corrects or replaces one is a new entry, and the old one gets a line saying "Superseded by the entry of <date>". So the file also records what was known when.

## Current picture

- **The schema we start from** is the one step 040 made on 2026-10-12: 60 entity classes, 104 predicates, 1,233 patterns. Every experiment on extraction (060) and evaluation (070) uses this same file. [Evidence](#2026-10-12--step-040--the-baseline-schema)
- **Step 040 gives a differently worded schema each time it runs**, even with almost nothing changed: in two runs, about a third of the entity classes and half the predicates were spelled differently (e.g. FileFormat in one, DataFormat in the other). So a change to 040 itself can only be judged after running the same setup several times, to see how much it varies on its own. [Evidence](#the-schema-varies-from-run-to-run)
- **150 texts are enough to find the entity classes, and nearly enough for the predicates** (the last 25 texts added 2.8), but not the patterns, which keep growing. The patterns are the part to trim before extraction runs on the whole catalog. [Evidence](#saturation)
- **Tables of numbers inside the `notes` field** (about 2% of records) are described, not copied cell by cell (rule 8 of *What counts as a fact* in the annotation guidelines). [Evidence](#data-tables-in-the-notes-field)
- **Whether LiteLLM passes an effort setting on to Claude isn't shown:** LiteLLM reads the effort value and refuses an invalid one, but with LiteLLM's answer cache bypassed, 3 requests of a counting puzzle per setting spent 758 completion tokens on average with no effort, 819 at `low` and 873 at `high`, the three settings' counts overlapping, and every answer was right. The runs keep the default effort, medium. [Evidence](#2026-11-01--litellm--the-effort-check-with-the-answer-cache-bypassed-the-effort-value-is-read-its-effect-not-shown), [earlier](#2026-10-31--litellm--whether-an-effort-setting-reaches-claude-not-shown), [the design](#2026-10-31--litellm--the-effort-check-could-not-answer-its-question-and-its-new-design)
- **Prompt caching** (paying a fraction for the part of a request that is the same every time) **works through NASA's LiteLLM for Claude**, the way 060 sends it. Extraction (060) uses it; nothing else repeats enough to be worth it. Its writes and reads fit several copies of the model, each with its own cache, so 060 now sends one session id per run, which keeps a run on one copy where the service allows it. Gemini gets no cache mark: a mark makes LiteLLM create a cache Google bills for storing, which explains Gemini's odd first read. [Evidence](#2026-10-12--litellm--prompt-caching-works-after-a-first-write-per-copy-of-the-model), [more](#2026-10-12--litellm--caching-inside-the-user-message-and-gemini), [copies](#2026-10-31--litellm--copies-of-the-model-that-dont-share-a-cache), [Gemini](#2026-10-31--litellm--why-gemini-read-a-cache-on-its-first-request)
- **Gemini 2.5 Pro's hidden thinking can use up the answer limit:** in 050's run of 2026-10-21, 79% of a cut-off answer's tokens went to thinking. 050 now caps the thinking (`--thinking`, default `low`); whether that makes drafts worse isn't measured yet. [Evidence](#2026-10-21--step-050--why-a-drafted-answer-was-cut-off)
- **The safety filter of the model's service** sometimes stops answers about space-biology phrases (e.g. "was more virulent than"). It is consistent with Anthropic's biology safety classifier, whose refusals are billed. Step 040 works around it; extraction (060) on space-biology records may lose some facts, to be watched in its report. [Evidence](#2026-10-12--step-040--what-the-content-filter-stopped-on), [more](#2026-10-31--model-service--what-the-content-filter-is)
- **data.nasa.gov changes by thousands of records within days:** 36,451 records today, 34 gone and 79 new since the harvest of 2026-10-01; a vanished record answers 403, which in CKAN means it is still in the database but not public. The project works from the harvest of 2026-10-01. [Evidence](#2026-10-31--datanasagov--records-that-vanish-and-the-count-today)
- **The Claude model's name is `claude-opus-5-5` since 2026-11-01**, the spelling NASA's LiteLLM lists. LiteLLM also accepts `claude-opus-5.5`, the spelling every run before that day used (the schema of 2026-10-12 among them); both answered on 2026-11-01, and whether they reach the same deployment is a question for LiteLLM's administrators. [Evidence](#2026-11-01--litellm--two-spellings-of-the-claude-models-name)
- **NASA's LiteLLM answers a repeated identical request from a cache of its own,** so without the bypass a recipe's repeats would be copies of one run. The bypass is on, on the NASA laptop, since 2026-11-01 (`LITELLM_BYPASS_ANSWER_CACHE=1` in `.env`): every LiteLLM request asks for a fresh answer. [Evidence](#2026-11-01--litellm--litellm-answers-repeated-requests-from-its-own-cache)
- **My LiteLLM account has a $25 budget, used up on 2026-11-02** (user `iiordane`, team `trial-moderate`; the service reported a cost of 25.0 to 27.05). No model can be called through LiteLLM until its administrators raise or reset it. [Evidence](#2026-11-02--litellm--the-budget-of-my-litellm-account-is-25-and-it-is-used-up)

## 2026-11-02 · LiteLLM · The budget of my LiteLLM account is $25, and it is used up

**What happened.** On the NASA laptop, on 2026-11-02, during `py helpers/second_judge.py` (after the weekend's runs of 2026-10-31 to 2026-11-02), NASA's LiteLLM answered model calls with HTTP 429 and bodies such as "Budget has been exceeded! User=iiordane in Team=trial-moderate Current cost: 25.0, Max budget: 25.0", and on other calls "… TeamMember=… Current cost: 27.04…". Across these answers the cost reported was 25.0 to 27.05, against a maximum budget of 25.0. Source: the service's own error messages; no spend was read from any other endpoint.

**What it means.** My LiteLLM account (user `iiordane`, team `trial-moderate`) has a spending cap of $25 that the service enforces, and the weekend's runs reached it. The spend reported passed the cap (27.05 against 25.0); the messages don't say why, so how far a run can overshoot it isn't known. Until the administrators raise or reset it, no model can be called through LiteLLM. The pipeline treated the answer as a passing rate limit and tried each call 4 times, in every worker, so the run kept sending calls; since this day, the first such answer stops the run at once (`docs/running_on_nasa_laptop.md`, *The budget is used up*). The cap also bounds every plan that needs the models before 2026-11-20: a run's cost has to be weighed against what is left of it (`docs/improvements.md`, *Cost per run from the service's own spend*).

## 2026-11-01 · LiteLLM · The effort check with the answer cache bypassed: the effort value is read, its effect not shown

**The test.** On the NASA laptop, on 2026-11-01, `py helpers/check_effort.py` through NASA's LiteLLM with `claude-opus-5-5`, twice: once before the answer cache's bypass was switched on, once after (the entry below). Step A: LiteLLM refused the invalid effort value "not_a_level" by its own validation, as on 2026-10-31, so it reads the effort setting and checks it. Step B, the counting puzzle (correct answer 168), 3 identical requests per setting, completion tokens:

| Sent | Before the bypass | After the bypass | Mean after |
|---|---|---|---:|
| no effort | 762, 762, 762 | 761, 738, 774 | 758 |
| `low` | 764, 764, 764 | 981, 731, 745 | 819 |
| `high` | 932, 932, 932 | 740, 1038, 840 | 873 |

Every answer after the bypass was right.

**What it means.** Before the bypass, each setting's three requests gave one count three times: copies from LiteLLM's answer cache (the entry below), so that run measured one answer per setting, and its verdict "passed on" (every `high` call above every `low` call) is void. After the bypass the counts vary from request to request, as they should from a model with adaptive thinking sent no temperature. The rule fixed before the calls says "passed on" only if every `high` call uses more completion tokens than every `low` call, or the mean of `high` is at least 1.5 times the mean of `low`: the lowest `high` count (740) is below the highest `low` count (981), and 873 is 1.07 times 819, so the verdict is "not shown". So LiteLLM reads and validates the effort value (step A), but whether the value changes how much the model thinks isn't shown, with this puzzle and 3 requests per setting. The runs keep the default effort, medium (`docs/improvements.md`, *Set Claude's effort explicitly*). This supersedes the entry of 2026-10-31 on the effort check run with its new design.

## 2026-11-01 · LiteLLM · LiteLLM answers repeated requests from its own cache

**The test.** On the NASA laptop, on 2026-11-01, `py helpers/check_answer_cache.py` through NASA's LiteLLM with `claude-opus-5-5`: one question ("Write one sentence about the Moon.", tagged with the check's time, so no earlier request was the same) sent twice as it is, then twice with LiteLLM's cache control `{"cache": {"no-cache": true, "no-store": true}}` (the check's design: `docs/improvements.md`, *Repeats that LiteLLM may answer from its own cache*).

| Call | Response header `x-litellm-cache-key` | Completion tokens | Answer |
|---|---|---:|---|
| plain 1 | none | 85 | the first answer |
| plain 2 | `22a06dbc…` | 85 | byte-identical to plain 1 |
| no-cache 1 | none | 48 | another answer |
| no-cache 2 | none | 64 | another answer again |

The proxy accepted the control (HTTP 200). The check's verdict, by its rule printed before the calls: "LiteLLM answers from its cache".

**What it means.** NASA's LiteLLM keeps answers and gives a repeated identical request the kept one, marked by the header LiteLLM's docs name ([LiteLLM caching](https://docs.litellm.ai/docs/proxy/caching)); a request carrying the control gets a fresh answer. This explains the identical counts of the effort check of 2026-10-31 (717, 717, 717; 814, 814, 814; 802, 802, 802) and of its first run on 2026-11-01 (the entry above): copies, not three answers. The same day, `LITELLM_BYPASS_ANSWER_CACHE=1` was added to the NASA laptop's `.env`, so every LiteLLM request of the pipeline carries the control, and each run's report says "LiteLLM answer cache: bypassed".

## 2026-11-01 · LiteLLM · Two spellings of the Claude model's name

**The question.** NASA's LiteLLM lists the Claude model as `claude-opus-5-5` (`py helpers/models.py`). The pipeline's default for 040, 060 and 070 was `claude-opus-5.5`, a spelling LiteLLM accepts but doesn't list, so `py helpers/models.py` warned that the default isn't in the list. Are both usable, and are they the same model?

**The test.** On the NASA laptop, on 2026-11-01, both spellings were tried through LiteLLM: both answered.

**What it means.** Both names are usable. Whether they reach the same deployment (one model behind two names, or two deployments behind two names) can't be told from outside, since NASA's routing isn't public: it is a question for NASA's LiteLLM administrators (question 2 of *Questions for NASA's LiteLLM administrators* in [`improvements.md`](improvements.md)). From this day on, the default of 040, 060 and 070 is the listed name, `claude-opus-5-5` (`MODEL` in `common/common_helpers/llm.py`), and `py helpers/models.py` marks it in the list without a warning. The code compares the two spellings as one model (`same_model_name` in `common/common_helpers/llm.py`): 060's warning that the ground truth of the records chosen was drafted by the extraction model still fires on the rows whose `drafted_by` is `claude-opus-5.5`, and says the name is spelled as the service also accepts it. What doesn't change: the `drafted_by` values already in the ground truth (history, as recorded); the schema of 2026-10-12, which was made with `claude-opus-5.5` ([the baseline schema](#2026-10-12--step-040--the-baseline-schema)); and every entry above this one, which names the spelling it ran with. What does: a cache key names the model as spelled, so a run under the new default asks everything again (paid), and the answers already saved stay valid under `--model claude-opus-5.5`; and two runs that differ only in the spelling are not repeats of one recipe to `py helpers/compare_runs.py`, since their `model` settings differ.

## 2026-10-31 · LiteLLM · The effort check, run with its new design: the effort value is read, its effect not shown

**The test.** On the NASA laptop, `py helpers/check_effort.py` through NASA's LiteLLM with `claude-opus-5.5`, the design of the entry below. Step A (an invalid effort value, "not_a_level") was refused by LiteLLM's own validation of the value, so LiteLLM reads the effort setting and checks it; it does not drop it. Step B (the counting puzzle, 3 identical requests per setting) gave these completion-token counts:

| Sent | Request 1 | Request 2 | Request 3 |
|---|---:|---:|---:|
| no effort | 717 | 717 | 717 |
| `low` | 814 | 814 | 814 |
| `high` | 802 | 802 | 802 |

**What it means.** The rule the check fixed before its calls says "passed on" only if every `high` call uses more completion tokens than every `low` call, or the mean of `high` is at least 1.5 times the mean of `low`: `high` used 802 against `low`'s 814, so the verdict is "not shown", and step B shows no measurable effect of the effort setting. The three requests of each setting gave exactly the same count. A model sent no temperature, with adaptive thinking, would vary from request to request, so the identical counts suggest that LiteLLM answered the repeated identical requests from a cache of its own (my reading, not shown). If so, step B's three requests per setting are one answer, and the check measured one call per setting. What follows from it is in `docs/improvements.md`, *Repeats that LiteLLM may answer from its own cache* (the check of the answer cache, `py helpers/check_answer_cache.py`, and its bypass). Superseded by the entry of 2026-11-01 on the effort check with the answer cache bypassed; the identical counts were copies from LiteLLM's answer cache (the entry of 2026-11-01 on that cache).

## 2026-10-31 · LiteLLM · The effort check could not answer its question, and its new design

**The flaw.** The check of the entry below asked one easy question. Anthropic says that with adaptive thinking "Claude determines whether and how much to think on each request, and at lower effort settings it might skip thinking entirely on easy inputs" ([Extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)). So the same 39 to 40 answer tokens at every effort are what both outcomes predict: the check could not tell a setting that reaches the model from one that is dropped. The visible answer bounds the thinking: Anthropic counts thinking inside the billed output tokens, so the thinking was at most a few tens of tokens.

**What narrows it, from the docs.** For Claude Opus 5.5, a request with a manual thinking budget or with thinking turned off returns HTTP 400 ([What's new in Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5)). The four requests succeeded, so LiteLLM either sent an effort or dropped the setting; it did not send an old-style thinking budget (my reading). Current LiteLLM maps `reasoning_effort` to Anthropic's `output_config` effort for Claude Opus 5.5, and says any other value "will raise a validation error" ([LiteLLM, Anthropic effort](https://docs.litellm.ai/docs/providers/anthropic_effort)); NASA's LiteLLM version is unknown.

**The new design** (`helpers/check_effort.py`, 2026-10-31; run later that day: the entry above). Step A sends `reasoning_effort` "not_a_level" and `output_config` effort "not_a_level": a refusal (4xx) means the setting is read, an answer (HTTP 200) that it was dropped or ignored, and the error text says whose check refused it. Step B asks a counting puzzle with a checked answer (168) 3 times each with no effort, at `low` and at `high`, and prints each call's completion tokens, the mean per setting and whether each answer is right. Its decision rule is fixed before the calls and printed first: "passed on" if every high call uses more completion tokens than every low call, or the mean of high is at least 1.5 times the mean of low; "not shown" otherwise, and also when a call failed. Completion tokens are the measure, since they include the thinking even where the service reports 0 reasoning tokens. Until it runs, the runs keep the default effort, medium.

## 2026-10-31 · LiteLLM · Why Gemini read a cache on its first request

**From the docs** (no new run). LiteLLM turns a `cache_control` mark sent to Gemini into Google's explicit context cache: it first creates a cached-content object from the marked messages, then sends the request with it ("the returned ID is passed as `cachedContent`"; "The cached content needs at least 1,024 tokens", [LiteLLM, prompt caching](https://docs.litellm.ai/docs/completion/prompt_caching)). So the first request of the test of 2026-10-12 read its whole prompt (1,930 tokens) from a cache LiteLLM had made a moment before. An explicit cache is billed for its storage ("If no TTL is specified, Google's default cache expiration (approximately 1 hour) applies", [LiteLLM's Gemini page](https://docs.litellm.ai/docs/providers/gemini)). Gemini 2.5 also caches an identical start of 2,048 tokens or more on its own, without a mark and at no cost ("Implicit caching is enabled by default for all Gemini 2.5 and newer models", [Google, context caching](https://ai.google.dev/gemini-api/docs/caching)).

**What it means.** The mechanism is documented; that it is what happened in that test is my reading, since no log of the proxy's calls was seen. The pipeline sends Gemini no cache mark: `_messages` (`common/common_helpers/llm.py`) marks a cached start only for Anthropic's models, and 050 asks for none. The same test's HTTP 500 has a documented mechanism too: Google's output limit includes the thinking, and Gemini 2.5 Pro's thinking can't be turned off, so a 20-token limit leaves no room for an answer; it stays unconfirmed from a log.

## 2026-10-31 · LiteLLM · Copies of the model that don't share a cache

**From the docs** (no new run). LiteLLM's default routing picks at random among the deployments that share a model name ("If rpm or tpm is not provided, it randomly picks a deployment"), and its docs advise session affinity "when the deployments behind a model group do not share state, for example provider-side prompt caching"; "The proxy reads it from the `x-litellm-session-id` header", and a pin lasts 3,600 seconds of idle time by default ([LiteLLM, routing](https://docs.litellm.ai/docs/routing)). Affinity is a setting of the proxy (`optional_pre_call_checks: ["session_affinity"]`).

**What it means.** The writes and reads of the entry of 2026-10-12 on prompt caching fit several deployments behind `claude-opus-5.5`, each with its own cache; it is still inferred, since NASA's routing isn't public. Since 2026-10-31, step 060 sends one `x-litellm-session-id` per run, the run's id, so that where the proxy has affinity on, a run's requests reach one deployment and read its cache. It changes no word sent and no cache key. The next 060 report's cache reads, compared with earlier runs', will show whether it takes effect.

## 2026-10-31 · Model service · What the content filter is

**From the docs** (no new run). Claude Opus 5.5 "runs a biology safety classifier in addition to the cybersecurity one" ([What's new in Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5)). A classifier's decline is not an error: "you receive a normal response, not an error, with `stop_reason: "refusal"`", and its category "bio" covers requests that "could enable biological harm"; "Beneficial life sciences work can also trigger this category". A refusal of that category is billed even when it arrives before any output, and "Re-sending a refused request to the same model usually results in another refusal" ([Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)). LiteLLM reports Anthropic's "refusal" as `finish_reason` "content_filter" (its `_FINISH_REASON_MAP`, `litellm/litellm_core_utils/core_helpers.py`, main branch, read 2026-10-31).

**What it means.** The two stops of run `040_induce_schema_2026-10-12_1629` are consistent with Anthropic's documented biology classifier: an HTTP 200 reply, reported as `content_filter`. It is not confirmed for those requests, since their refusal category was not recorded, and LiteLLM's code shows no handling of Anthropic's `stop_details`, so the category is probably lost on the way (my reading). Whether NASA's proxy adds filters of its own is not known. Asking again in halves worked because it changed the input, which asking the same request again would not. Each refused record costs a billed call.

## 2026-10-31 · data.nasa.gov · Records that vanish, and the count today

**What a 403 means.** data.nasa.gov runs CKAN 2.11.7 (its `status_show`). In CKAN 2.11, `package_show` answers an anonymous caller with 403, "User  not authorized to read package <id>", for a dataset that is still in the database but is not active and public: deleted (CKAN's `package_delete` keeps the row, "it will no longer show up in the front-end, but is still in the db"), a draft, or private. A 404 comes only for a dataset no longer in the database ([CKAN 2.11 source](https://github.com/ckan/ckan/tree/2.11): `ckan/logic/auth/get.py`, `ckan/views/api.py`, `ckan/logic/action/delete.py`). Deleted and private can't be told apart from outside. So the 12 records of 20 that answered 403 on 2026-10-11 still existed, hidden. That day's count "with private and draft records asked for" could not show more: CKAN returns an anonymous caller none of them (`package_search`'s `include_private` and `include_drafts`). This assumes data.nasa.gov keeps CKAN's default permissions; the message matches the default word for word.

**The count today.** 36,451 records (37 pages of ids and dates only, the same count on every page). Against the harvest of 2026-10-01 (36,406 records), 34 ids are gone, all maintained by "NASA Space Physics Data Facility" and created in August or September 2026, and 79 are new, created on 2026-10-05, 2026-10-12 and 2026-10-20. Of the 32 gone records outside the ground truth candidates pool, 28 answered that 403 and 4 timed out. Two records of the pool (positions 163 and 754, not annotated) are among the gone. Of the 36,375 ids of the harvest of 2026-09-27, 36,339 are listed now, so the count of 14,672 on 2026-10-11 was temporary. 14,090 records were modified on 2026-10-27 and 4,533 on 2026-10-26.

**What it means.** The catalog runs CKAN's harvest extensions (`harvest`, `ckan_harvester`, `datajson_harvest`, `dcat_rdf_harvester`), whose import stage may "create, update or delete a CKAN package" ([ckanext-harvest](https://github.com/ckan/ckanext-harvest)). Harvest jobs that delete records and bring them back would explain the swings in the count (my reading; the catalog's harvest schedule wasn't found). The project keeps working from the harvest of 2026-10-01, which this supports: the live catalog changes by thousands of records within days.

## 2026-10-31 · LiteLLM · Whether an effort setting reaches Claude: not shown

**The test.** On the NASA laptop, `py helpers/check_effort.py`: one small question to `claude-opus-5.5` through LiteLLM, asked four ways. The service accepted all four and every answer was "247":

| Sent | Answer tokens | Thinking tokens reported |
|---|---:|---:|
| no effort | 40 | 0 |
| `reasoning_effort` low | 39 | 0 |
| `reasoning_effort` high | 40 | 0 |
| `output_config` effort high | 40 | 0 |

Prompt: 67 tokens each; no cache read or write.

**What it means.** `high` spent no more tokens than `low`, so this test doesn't show that LiteLLM passes an effort setting on. It doesn't show the opposite either: the question is easy enough that the model may think as little at any effort, and a thinking count the service reports as 0 is unknown, not zero (the entry of 2026-10-12 on the content filter). A question that needs several steps of reasoning would tell the two apart. Until one does, the runs keep the model's default effort, medium, and their records say `effort: not sent (model default, medium)`.

The check could not answer its question: with adaptive thinking, the model may skip thinking on an easy question at any effort, so equal token counts are what both outcomes predict (design fixed on 2026-10-31; see [the entry of 2026-10-31 on the effort check](#2026-10-31--litellm--the-effort-check-could-not-answer-its-question-and-its-new-design)).

## 2026-10-21 · Step 050 · Why a drafted answer was cut off

**The run.** On the NASA laptop, `py 050_annotate/run.py --records_per_batch 2`, model `gemini-2.5-pro` through LiteLLM, no thinking setting sent, answer limit 16,000 tokens (`MAX_ANSWER_TOKENS` in `common/common_helpers/llm.py`). Record d5477563-0415-4e65-ab7c-d4bc9ed809e5 (a 1,503-character text, one text piece) failed: its answer was cut off after 10,623 characters. The log (`outputs/logs/050_annotate_2026-10-21_1443.log`, line 35) gives the service's token counts.

**The numbers.** 15,996 answer tokens in all: 12,615 (79%) of Gemini 2.5 Pro's hidden thinking and 3,381 of visible answer. Prompt: 4,872 tokens.

**What it means.** The cause is confirmed: the thinking, which counts against the answer limit, used most of it, leaving the visible answer too few tokens to finish. The 3,381 visible tokens for 10,623 characters (about 3.1 characters a token) are ordinary. It doesn't show whether the visible answer repeats itself, nor whether less thinking drafts worse; those are in `docs/improvements.md` (050).

## 2026-10-12 · LiteLLM · Caching inside the user message, and Gemini

**The test.** On the NASA laptop, the same 2,523-token block as in the entry below, this time marked for caching as the first part of the user message (not a separate system message), sent 4 times to `claude-opus-5.5` and 4 times to `gemini-2.5-pro`, each with an answer limit of 20 tokens.

**Claude.** All 4 requests wrote the cache (2,524 tokens), none read it. With the block as a separate system message (the entry below), 4 of 8 read it. Four writes in a row could still be four different copies of the model, so this doesn't prove the user-message form never reads; but only the system-message form has been seen to read, so 060 keeps that form. 040's requests for triple instances get no caching: its saving would be small (about 150 requests with a 1,000–2,000-token identical start), and its requests stay as the baseline run sent them.

**Gemini.** The first request answered and reported its whole prompt (1,930 tokens) as read from a cache, though Gemini had not been sent it before; why isn't known. The next three failed: HTTP 500 from LiteLLM, "provider returned a response with no 'choices'". A likely but unverified cause is the 20-token answer limit: Gemini 2.5 Pro thinks before answering and its thinking counts against the limit, so it may have used all 20 before writing anything. 050's requests allow 16,000 tokens (`MAX_ANSWER_TOKENS`). If 050 meets the same error, it would cost calls: an HTTP 500 is asked again (`RETRY_STATUSES` in `common/common_helpers/llm.py`); each report now counts every request, which would show it. 050 asks for no caching.

Superseded in part by [the entry of 2026-10-31 on Gemini's cache](#2026-10-31--litellm--why-gemini-read-a-cache-on-its-first-request): the first-request cache read is what LiteLLM's explicit caching for Gemini does, and the HTTP 500 has a documented mechanism (still unconfirmed from a log).

## 2026-10-12 · LiteLLM · Prompt caching works, after a first write per copy of the model

**The test.** On the NASA laptop, identical requests to `claude-opus-5.5` through NASA's LiteLLM, each starting with the same 2,523-token block marked for Anthropic's prompt caching. First two requests: both wrote the cache, neither read it. Then six more, in this order: read, read, wrote, wrote, read, read (2,523 tokens each time).

**Interpretation.** The caching instruction reaches the model's service, and cached reads happen. That the first requests wrote and later ones read, with writes reappearing between reads, fits several copies of the model behind the service, each with its own cache that is written once and then read; this is inferred, not confirmed by the service. Since writing costs 1.25 times normal input and reading 0.05 times (for Opus 5.5, per Anthropic's documentation), caching pays once about 1 request in 5 reads: here 4 of 8 did, and in a long run nearly all would. 060 asks for caching since (`060_extract/060_extract.md`, *The schema in the prompt*), and each report counts the tokens read from and written to the cache, which will show the real share.

See also [the entry of 2026-10-31 on copies of the model](#2026-10-31--litellm--copies-of-the-model-that-dont-share-a-cache): LiteLLM's docs describe this pattern, deployments that don't share a cache, and a header that keeps one run on one deployment.

## 2026-10-12 · Step 040 · What the content filter stopped on

**The evidence.** In run `040_induce_schema_2026-10-12_1629`, its log (`outputs/logs/040_induce_schema_2026-10-12_1629.log`, DEBUG lines starting "answer stopped by the service") holds what the model wrote before each of the two stops, both in stage 3's predicate labeling. The last words before the first (a batch of 80, 699 characters): `"was grown in LSMMG using": "USES", "was grown`. Before the second (a batch of 40, 163 characters): `"was more virulent than": "COMPARED_TO", "was observed in": …`. LSMMG is low-shear modeled microgravity, a way of growing microbes; both phrases come from GeneLab's space-biology records (how bacteria behave in spaceflight). The service reported no thinking tokens; for Claude through LiteLLM that may mean the count wasn't reported rather than that none were spent (Claude Opus 5.5 always thinks: [What's new in Claude Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5)), so how much it thought is unknown.

**A hypothesis, not verified.** A safety filter for biological content: recent Anthropic models run with classifiers that block content on making pathogens more dangerous, and a list of bare phrases such as "was more virulent than" and "was grown in … using", without their records, can look like that. Smaller batches, where such phrases are fewer, went through. Whose filter it is (the model maker's, or one added by the service LiteLLM forwards to) isn't known, nor whether every such stop is labeled `content_filter`.

**Interpretation.** For 040, nothing more: asking again in halves got every batch answered. For 060, which extracts from whole records (in 040, every text's extraction went through), failed records clustering in GeneLab's would point to the same filter; 060's report lists every failed record.

Superseded in part by [the entry of 2026-10-31 on the content filter](#2026-10-31--model-service--what-the-content-filter-is): the stops are consistent with Anthropic's documented biology classifier. Corrected on 2026-10-31: "Claude Opus 5.5 always thinks" (above) is not Anthropic's wording; adaptive thinking is always on, and the model decides whether and how much to think, and may skip it on easy inputs ([Effort](https://platform.claude.com/docs/en/build-with-claude/effort); [Extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)).

## 2026-10-12 · Step 040 · The baseline schema

**The run.** `040_induce_schema_2026-10-12_1714`, on the NASA laptop: the harvest of 2026-10-01; `claude-opus-5.5` through LiteLLM; 15 texts from each of the 10 largest maintainers (150 texts); `min_support` 1; the extraction rules with rule 8 of *What counts as a fact* (values inside a data table aren't facts). It found 2,767 verified triple instances in 150 texts, and made a schema of 60 entity classes, 104 predicates, and 1,233 patterns. This is the baseline schema: 060's and 070's experiments use this file unchanged. Its report: `outputs/reports/040_induce_schema_2026-10-12_1714.md`.

### The schema varies from run to run

The run before it, `040_induce_schema_2026-10-12_1629`, had the same setup except rule 8 of *What counts as a fact* (its schema and evidence are kept in `outputs/intermediate_results/040_induce_schema/previous_runs/040_induce_schema_2026-10-12_1629/`). Rule 8 changes what about 3 of the 150 texts give, yet:

| | Before rule 8 | After | Spelled the same in both |
|---|---:|---:|---:|
| Entity classes | 63 | 60 | 41 |
| Predicates | 126 | 104 | 67 |

Most of the difference is one entity class or predicate with a different label: `FileFormat` → `DataFormat`, `Resolution` → `SpatialResolution`, `Substance` → `Chemical`, `Publication` and `ResearchPaper` → `Paper`, `RELEASED_ON` → `RELEASE_DATE`, `UPDATED_ON` → `LAST_UPDATED`.

*What it means.* The induced schema is not reproducible from run to run: the model chooses different labels, and the first labels chosen shape later ones (stage 3's running vocabulary). So an experiment that changes 040 itself (its sample, `min_support`, its prompts) needs the same recipe run several times, to see how much the schema moves by chance alone, before a difference can be called an effect.

*What it doesn't mean.* The two runs differ by rule 8 and by chance, so this comparison can't separate the two; only a repeat of one recipe can (it needs a setting that asks the model again instead of reusing the cache, not built yet). Comparing by spelling also overstates the difference, since an entity class or predicate with a new label counts as a loss and a gain; a fair comparison would first match labels that mean the same thing (not designed yet). It doesn't affect experiments on 060 or 070, which use the baseline schema unchanged.

### Saturation

From the run's report (*Saturation*): the expected number of schema entries after k of the 150 texts, averaged over every reading order.

| Texts read | 25 | 50 | 75 | 100 | 125 | 150 | Added by the last 25 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Entity classes | 54 | 58 | 60 | 60 | 60 | 60 | 0.01 |
| Predicates | 71 | 86 | 94 | 99 | 102 | 105 | 2.8 |
| Patterns | 297 | 537 | 746 | 934 | 1,106 | 1,264 | 158 |

Both tables count by support only, before stage 7 leaves out the entries too vague to define, so they end at 105 predicates and 1,264 patterns, one predicate and 31 patterns more than the schema has.

Entity classes are saturated: more texts from these 10 maintainers would find no new entity classes. Predicates nearly are. Patterns are not, and with `min_support` 1 likely never will be: every pattern seen once counts. This speaks only for the 10 maintainers read.

### Breadth

| Schema entries found in texts of | 1 maintainer | 2 | 3 or more |
|---|---:|---:|---:|
| Entity classes | 2 | 9 | 49 |
| Predicates | 24 | 14 | 67 |
| Patterns | 1,067 | 145 | 52 |

Entity classes and most predicates are shared across maintainers, a hint that the 412 maintainers not read use them too. Most patterns come from one maintainer: patterns local to it, which fits their curve. Both point to patterns as the part of the schema to make stricter, e.g. by `min_support` (an experiment to make before 060's run on the whole catalog, whose every prompt includes the schema).

### Data tables in the `notes` field

In the run before (`_1629`), one record's answer (`2346cc06-9a33-471e-b30d-ac41fa072be6`, "Chandra Point Sources in 18 Distant Galaxy Clusters", 4,230 characters) was cut off at the 16,000-token limit after 26,399 characters: not a loop, but 164 distinct triple instances, one per cell of an 18-row table (redshift, position, exposure time of each cluster); the service reported no thinking tokens, which for Claude may mean they weren't reported, so how much of the limit thinking used is unknown (the limit is 32,000 since 2026-10-30). About 2% of the catalog's records (766, by a rough pattern for table-like lines) have such tables. Rule 8 (`annotations/guidelines.md`, *What counts as a fact*) now keeps what a table is about and leaves out its cells; under it the same record gave 29 triple instances and fit.

### The service's content filter

In both runs, the service behind LiteLLM withheld some answers of stage 3's predicate labeling (`finish_reason` `content_filter`). The batches were asked again in halves (`common/common_helpers/cache.py`, `ask_split`) down to batches of 2, and in the end nothing was refused: smaller batches went through. What sets the filter off, and whose filter it is, isn't known. Superseded in part by the entry of 2026-10-12, *Step 040 · What the content filter stopped on*.
