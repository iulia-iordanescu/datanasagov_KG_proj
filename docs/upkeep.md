# Upkeep

Everything a person does to keep the project going, grouped by when it comes up. To see what is waiting right now, run `py run_pipeline.py --status`, or open the [annotation tool](terminology.md#4-ground-truth-and-samples) (`py helpers/annotate.py`): both read the files and list what to do next, each item with its section here. Every pipeline report ends with the same list. How to do each thing is in the document each item names; this page says what to do, and when.

The terms: [`terminology.md`](terminology.md).

## Before the first run

- **Set up the computer:** Python, the environment, the packages, and the `.env` file with the model's service key ([`virtual_environment_setup.md`](virtual_environment_setup.md)). On the NASA laptop, follow [`running_on_nasa_laptop.md`](running_on_nasa_laptop.md) from the top.
- **On another computer, copy the saved harvest first:** the folder `outputs/intermediate_results/010_harvest/`. Git doesn't carry `outputs/`, and running step 010 without it would harvest the catalog as it is that day, no longer the catalog of 2026-10-01. With the folder copied, 010 keeps it and asks the catalog nothing.
- **A trial harvest** (`--max_records`) only checks that harvesting works: step 030 writes `outputs/intermediate_results/030_split/splits.json` only once, so it won't split a trial catalog. Run the full harvest before steps 020 and 030.
- **Choose the models** before the real runs, since every saved answer is tied to its model ([`running_on_nasa_laptop.md`](running_on_nasa_laptop.md), *Choosing a model*): for 040, the strongest one the service lets you use; for 050, the strongest one too, from a different maker than extraction's; for 060, from a different maker than 050's, and for the run over every record, the cheapest whose metrics are within the [margin of error](../070_evaluate/metrics/approximately.md) of the best.
- **Make the test run** ([`running_on_nasa_laptop.md`](running_on_nasa_laptop.md), *Test run first*): about 20 [paid calls](terminology.md#8-the-pipeline) that show everything works.
- **Before each extraction (step 060), read what the model is given:** the rules, `common/common_prompts/extraction_rules.txt`, which should say what the [annotation guidelines](terminology.md#4-ground-truth-and-samples) (`annotations/guidelines.md`) say, and the step's prompts ([`060_extract.md`](../060_extract/060_extract.md), *Prompts*). The rules change while annotating, and the model follows only its own copy.

## Running the steps again

- **Run the steps in order** (`py run_pipeline.py`, or `py <step>/run.py` one at a time). A step needs what the steps before it wrote.
- **A step is out of date** when an input it read has changed since its run; the status says which input. Run it again with the steps after it: `py run_pipeline.py --from <step number>`. Step 030 is the exception: `splits.json` is written once and then kept, so running it again only checks that the split still holds, and warns if a new draw would differ. Delete `splits.json` only if you mean to rebuild the split (e.g. after a new harvest); the pool's order and parts stay the same.
- **Before a step pays for [model calls](terminology.md#8-the-pipeline),** read what it prints: anything it can't do exactly as asked is listed above the question. Press Enter to go ahead (every answer it takes: [`running_on_nasa_laptop.md`](running_on_nasa_laptop.md#5-the-steps-that-cost-money-040-050-060-070), section 5).
- **After each step, read its report's Warnings** (`outputs/reports/<step>_<date>_<time>.md`; the step prints the path when it ends). Each warning is explained, with what to do, in that step's guide, *Checks and warnings*.
- **After step 040, review the merges** listed in its report (section *Triple instances and labels*), and the [spelling folds](terminology.md#3-schemas) in `outputs/intermediate_results/040_induce_schema/induction_evidence.json` (under `spelling_folds`). A wrong merge (two different ideas made one) is the one mistake code can't catch: it just looks like a single [entity class](terminology.md#3-schemas) with high support. Also read the report's *Saturation*: if the last 25 texts still added several schema entries, the sample may be too small for its maintainers; if many schema entries come from one maintainer only, it may read too few maintainers. Either is a change to test against this run (`helpers/compare_runs.md`), not to make on sight.
- **Never edit or reorder `annotations/ground_truth_candidates.csv`** (the pool): its order is what makes the [ground truth](terminology.md#4-ground-truth-and-samples) a [fair sample](terminology.md#4-ground-truth-and-samples).

## After step 050 drafts a batch

Step 050 drafts the next [drafted batch](terminology.md#4-ground-truth-and-samples) only when none is waiting: a drafted batch not opened yet, or a [ground truth](terminology.md#4-ground-truth-and-samples) file with a record not finished.

- **Correct the drafted batch in the [annotation tool](terminology.md#4-ground-truth-and-samples)** (`py helpers/annotate.py`, *Ground truth*), following the [annotation guidelines](terminology.md#4-ground-truth-and-samples) ([`annotations/guidelines.md`](../annotations/guidelines.md)): read each record's text first, then fix, delete, or add ground truth triples until every fact it states is there, and tick *All facts extracted*. The tool saves to `annotations/ground_truth/batch_<NNN>.csv`; never correct the drafted batch's own file (`outputs/intermediate_results/050_annotate/drafted_triples_batch<N>.csv`), which can be deleted and rebuilt.
- **Add the facts the [drafted triples](terminology.md#4-ground-truth-and-samples) missed**, above all. Keeping a wrong drafted triple is easy (reading the text first, then the ground truth triples, limits it); a fact the model missed is unlikely to be added by hand, and if extraction doesn't extract it either, it never becomes a ground truth only triple: recall comes out higher than it should.
- **Draft and correct drafted batches in pool order, without skipping:** a record after a gap falls out of the [fair sample](terminology.md#4-ground-truth-and-samples), the only records evaluation evaluates.
- **Annotate tuning and [held-out records](terminology.md#7-evaluating-extraction-step-070) the same way.** The tool shows each record's part; it matters only for [entity classes](terminology.md#3-schemas) and predicates you'd add to the [schema additions](terminology.md#3-schemas) (*After step 060*).

## While annotating

- **An [entity class](terminology.md#3-schemas) or predicate you coin:** add it with a one-line definition to the [ground truth schema](terminology.md#3-schemas) (`annotations/ground_truth_schema.txt`): in the tool, the button under its ✖, or **Help → Ground truth schema**. Until then the next [drafted batches](terminology.md#4-ground-truth-and-samples) reuse it without a definition, the tool marks it as an error (it could be a typo), and step 070 stops while a [finished record](terminology.md#4-ground-truth-and-samples) uses it. If it's a typo, fix it where it's used instead.
- **A pattern used for the first time** (⚑): check the entity classes and the direction. If it's right, there's nothing to do: the ground truth schema's patterns include every one the [ground truth](terminology.md#4-ground-truth-and-samples) uses.
- **Every ✖ in the tool** (each one: `050_annotate/050_annotate.md`, *Checks on each row*): fix it.
- **To rename an entity class or predicate of the ground truth schema, merge two that mean the same thing, or change a definition:** in the tool, **Help → Ground truth schema**, then **Edit definitions, rename, or merge…** ([`annotations/README.md`](../annotations/README.md), *The ground truth schema*). It changes every file at once, after showing what it would change.

## After step 060

- **Run step 060 again after finishing more [ground truth](terminology.md#4-ground-truth-and-samples) records:** by default it extracts only the finished ones, and evaluation can evaluate only what it extracted.
- **Read its report's table *[Component classes](terminology.md#3-schemas) outside the schema*** (also listed in the tool, *Schema additions*): [entity classes](terminology.md#3-schemas) and predicates the model used that the [current schema](terminology.md#6-extracting-with-a-schema-step-060) doesn't have, from [tuning records](terminology.md#7-evaluating-extraction-step-070) and records outside the ground truth only (never held-out ones), so every one listed is fair to add. For one that keeps coming back and names a real type of thing or relationship, add it to `annotations/schema_additions.txt` with a one-line definition and the `source:` line the table gives (in the tool, its *Add* button).
- **Give every [schema entry](terminology.md#3-schemas) of `annotations/schema_additions.txt` a `source:` line.** One learned from the ground truth must come from tuning records only, named by [pool position](terminology.md#4-ground-truth-and-samples) (`source: ground truth tuning #12`); step 060 leaves out any other. Add to the [schema additions](terminology.md#3-schemas) only from the [tuning part](terminology.md#7-evaluating-extraction-step-070), or from outside knowledge: adding entity classes or predicates because of what [held-out records](terminology.md#7-evaluating-extraction-step-070) need is tuning on them.
- **Now and then, read the removed [classed triples](terminology.md#2-triples)** (`outputs/intermediate_results/060_extract/extracted_triples_removed.csv`, each with its reason). A check that removes correct classed triples is a sign the schema, or the prompt, needs work.

## When step 070 stops

Step 070 stops, before evaluating, while something it needs from a person is missing. Do each, then run it again.

- **An [entity class](terminology.md#3-schemas) or predicate a [finished record](terminology.md#4-ground-truth-and-samples) coined** isn't in the [ground truth schema](terminology.md#3-schemas): add it (*While annotating*), or fix the typo.
- **Rows of the [translation table](terminology.md#7-evaluating-extraction-step-070) to check:** step 070 adds a row for each [component class](terminology.md#3-schemas) of the [current schema](terminology.md#6-extracting-with-a-schema-step-060) that has none (the model proposes each, one [paid call](terminology.md#8-the-pipeline) per 100), then stops. Check each in the tool (*Translation table*), which shows both definitions and an example [extracted triple](terminology.md#6-extracting-with-a-schema-step-060). A wrong translation silently turns right extracted triples into wrong ones, or the reverse.
- **Rows that stop it, and rows it only warns about:** which is which, for each [row state](terminology.md#7-evaluating-extraction-step-070): *row state* in [`terminology.md`](terminology.md#7-evaluating-extraction-step-070). What to do: stale (a definition changed since the row was checked): check it again; repeated: keep one row per component class; translating to an entity class or predicate no longer in the ground truth schema (after a rename by hand, say): choose the right one; a value outside those a column takes (a hand edit): fix it, as the message says.
- **Now exists or suggested** (a row that says `(none)` though the ground truth schema has since gained a counterpart): choose it if it means the same.

## After step 070

- **Review the [partial pairs](../070_evaluate/metrics/pairs.md)** of the [tuning part](terminology.md#7-evaluating-extraction-step-070) (in the tool, *Partial pairs*): mark each *Same fact* or *Not the same fact*, with the record's text at hand. Then run step 070 again: the verdicts change its numbers.
- **Read its report's *Component class mismatches*:** it's how a wrong row of the [translation table](terminology.md#7-evaluating-extraction-step-070) shows up, even one already checked. Also read *The translation table*: [component classes](terminology.md#3-schemas) that share a translation are ones the metrics can't tell apart; if that distinction matters, make it in the [ground truth](terminology.md#4-ground-truth-and-samples).
- **Read `outputs/intermediate_results/070_evaluate/per_record.md`**, especially the partial pairs and the occurrences left extracted only ("Extracted only"): some may be real facts missed while annotating. Add those only to [tuning records](terminology.md#7-evaluating-extraction-step-070) (fixing the ground truth from extraction's answers favors extraction).
- **Margins of error need at least 20 finished tuning records;** until then, read `per_record.md` rather than the numbers.
- **To know whether a change helped** (another model, prompt, rule, or schema), evaluate both versions on the same finished tuning records and compare them: `py helpers/compare_runs.py <run id> <run id>` ([`helpers/compare_runs.md`](../helpers/compare_runs.md)).
- **Report any metric** against this ground truth as such: drafted by a model and corrected by a person, not written from scratch.

## At the end: the held-out part

- **Look at the [held-out part](terminology.md#7-evaluating-extraction-step-070) only at the end** (`py 070_evaluate/run.py --evaluate_held_out true`). Each look is logged in `annotations/held_out_looks.csv`: commit it after each look.

## After every session

- **Commit every changed file in `annotations/` to Git, and push**, so the work is safe and reaches the other computer (`git pull` there before working).
- **Saved answers and [drafted batches](terminology.md#4-ground-truth-and-samples) stay on the computer that made them:** `outputs/` isn't in Git. A drafted batch made on the NASA laptop is annotated there, or its file copied over first.
