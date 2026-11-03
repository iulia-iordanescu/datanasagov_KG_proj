# Start here

This project builds a [knowledge graph](terminology.md#8-the-pipeline) from the metadata [records](terminology.md#1-records-and-their-text) of [data.nasa.gov](https://data.nasa.gov): a language model learns a [schema](terminology.md#3-schemas) from the records and extracts [classed triples](terminology.md#2-triples) with it. I evaluate the extraction against a [ground truth](terminology.md#4-ground-truth-and-samples) I corrected by hand, and the evaluation separates the facts the schema can't state from the facts extraction misses.

I wrote this page for whoever continues the project after my internship ends on 2026-11-20, when my model access ends too. Each fact below has one home, which the page links to.

## What exists

- **Steps 010 to 070 work** and run in order (`py run_pipeline.py`): harvest, clean, split, learn the schema (040), draft the ground truth (050), extract (060), evaluate (070). Each step's guide is `<step>/<step>.md`; the [README](../README.md) lists every file and folder.
- **Eleven helpers** in `helpers/`, each with its row in the README: the [annotation tool](terminology.md#4-ground-truth-and-samples) (`py helpers/annotate.py`), comparing runs, the [second opinion](terminology.md#4-ground-truth-and-samples) and the [second judge](terminology.md#4-ground-truth-and-samples), and others.
- **Step 080, building the graph itself, is not built.** What it must do is listed in [`improvements.md`](improvements.md#080_build_graph), section *080_build_graph*.

## How to run it

- **Where:** the NASA laptop, through NASA's LiteLLM: [`running_on_nasa_laptop.md`](running_on_nasa_laptop.md), from getting the code to the steps that pay.
- **What pays:** steps 040 to 070 and the helpers that call a model ask before their first paid call and give the count to pay. Every other command is free by code, and a rerun is free when every answer is in a cache ([`running_on_nasa_laptop.md`](running_on_nasa_laptop.md), *When a rerun is free*). My LiteLLM budget is used up ([`findings.md`](findings.md), *Current picture*), so only free commands run until it is raised.
- **Checking the TM's numbers:** `py helpers/reproduce_results.py` makes the six runs the NASA TM quotes again, for free, and says for each number whether it is still the same ([`helpers/reproduce_results.md`](../helpers/reproduce_results.md)). It needs the laptop's `outputs/` folder, which isn't in Git.
- **What is waiting for a person:** `py run_pipeline.py --status` ([`upkeep.md`](upkeep.md)).

## Where things are written down

- **Results and what they mean:** [`findings.md`](findings.md), its *Current picture* first.
- **Decisions, open work, and what was considered and not changed:** [`improvements.md`](improvements.md), by step.
- **The terms:** [`terminology.md`](terminology.md). Every doc uses these words only.
- **Work made by a person:** `annotations/`, in Git and never regenerated: the ground truth, the [ground truth schema](terminology.md#3-schemas), the [annotation guidelines](terminology.md#4-ground-truth-and-samples), the [translation table](terminology.md#7-evaluating-extraction-step-070), the partial-pair [verdicts](terminology.md#7-evaluating-extraction-step-070), and the questions for experts ([`annotations/README.md`](../annotations/README.md)).

## Open work, most important first

Each item is in [`improvements.md`](improvements.md), under the section named, with why it matters and what it needs.

1. **Run the second judge** once the budget allows (*050_annotate*, *A blind second judge of my decisions*): it measures how far my decisions on the second opinion's facts and on the partial pairs can be reproduced.
2. **Review the second opinion's 50 new facts** (*050_annotate*, *The second opinion's 50 new facts to review*), then score again for free.
3. **Decide the component class mismatches seen again and again** (*070_evaluate*, *Component class mismatches seen again and again in the final re-score*): for each, a row of the translation table or a habit of extraction or of the ground truth.
4. **A count that keeps what it counts** (*060_extract*, *A count without what is counted*): extraction wrote "186" where the record says "186 parameters".
5. **Annotate the held-out part and evaluate it once**, at the end, with the rules frozen: `py 070_evaluate/run.py --evaluate_held_out true` ([`070_evaluate.md`](../070_evaluate/070_evaluate.md)); how held-out records are annotated is in *050_annotate*, *Held-out records may coin entries, marked held-out only*. A record that step 060 never extracted can't be evaluated without model access (*The whole pipeline*, *Extract and draft, before model access ends, every record that could ever be evaluated*).
6. **Build step 080** (*080_build_graph*), starting with telling apart one name that means two things (*One name, two things*).

## What still assumes data.nasa.gov

The method is meant to carry over to other catalogs, but these parts still assume data.nasa.gov ([`improvements.md`](improvements.md#the-whole-pipeline), *Other catalogs*, which also plans a design review and a transfer test):

- the catalog's address is fixed in `010_harvest/010_harvest_helpers/ckan_client.py`, and the harvest uses CKAN's `package_search`;
- step 020 treats "undefined" as a maintainer (`020_clean/020_clean_helpers/maintainers.py`), and the split into strata needs a maintainer field other catalogs may not fill;
- step 040's prompts say "a catalog of NASA datasets";
- rule 1 of the annotation guidelines, *Names on an official NASA list*, gives a name the record doesn't explain its entity class only from NASA's lists (the Global Change Master Directory's keywords, or the Planetary Data System's);
- the ground truth, the ground truth schema, the translation table and the rules were written for this catalog's records, so another catalog needs a ground truth of its own before it can be evaluated.
