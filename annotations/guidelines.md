# Annotation guidelines

What to write in the [ground truth](../docs/terminology.md#4-ground-truth-and-samples), and how, so that anyone annotating a record writes the same [classed triples](../docs/terminology.md#2-triples). For how to use the [annotation tool](../docs/terminology.md#4-ground-truth-and-samples) (`py helpers/annotate.py`), see [README.md](README.md), *Annotating ground truth: the annotation tool*. Terms: [docs/terminology.md](../docs/terminology.md).

The ground truth is the answer key extraction (step 060) is evaluated against (step 070). So every rule below is also a rule the model follows when it drafts (step 050) and extracts (step 060): the shared rules in `common/common_prompts/extraction_rules.txt`. A ground truth written by other rules would count extraction wrong where it followed its own.

## Before you start

- **Work in pool order, without skipping.** [Draft batches](../docs/terminology.md#4-ground-truth-and-samples) with `py 050_annotate/run.py` and correct them in the order of the pool: a record after a gap isn't evaluated until the records before it are done (`050_annotate/050_annotate.md`, *To do*).
- **Read the record's text first, then its ground truth triples.** The draft was written by a model: reading the text first makes it easier to see what the draft got wrong, and above all what it missed.
- **Annotate tuning records and held-out records the same way.** The tool shows each record's part; it changes nothing about how you annotate.

## What counts as a fact

1. **Only what the record states.** Never add what you know from elsewhere, and never guess what an unexplained code or acronym stands for.
2. **Every fact the record states**, whether or not the [ground truth schema](../docs/terminology.md#3-schemas) has words for it. Leaving a fact out is the worst mistake: a fact missing from the [ground truth](../docs/terminology.md#4-ground-truth-and-samples) counts extraction wrong when it finds that fact (lower precision), and makes recall look better than it is when it misses it too; nothing else catches it.
3. **Not the field names.** The record's text is split into fields (`title:`, `notes:`, …); the names are formatting, not facts.
4. **Not "is a" facts.** "MODIS is a spectroradiometer" says what kind of thing MODIS is: that belongs in its [entity class](../docs/terminology.md#3-schemas), not in a [classed triple](../docs/terminology.md#2-triples) of its own.
5. **Not opinions.** Leave out words such as "great".
6. **Not negated facts.** A [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) always says that something is so; it can't say "not". *Suppose:* a record says "Data are not available before 2001." *Then:* no ground truth triple. A ground truth triple with the [object instance](../docs/terminology.md#2-triples) "before 2001" would say the data are available before 2001, the opposite of the text. Don't rewrite it as "available from 2001" either: the text doesn't say that, it only follows from it. No ground truth triple means the graph says nothing about it, which is not the same as saying it's false.
7. **Not uncertain facts.** *Suppose:* a record says "The collection may include data from Terra." *Then:* no ground truth triple: the record doesn't state that it does. The same for "might", "possibly", "is expected to". A value given as approximate is stated, though: *suppose* a record says "a resolution of approximately 250 m"; *then* that is one ground truth triple, with "approximately 250 m" as its object instance.
8. **Not the values inside a data table; only what the table is about.** Some descriptions include a table of measurements. *Suppose:* a record says "Table 1 lists, for each of the 18 clusters, its redshift, position and exposure time", followed by rows such as "RDCSJ 1317+2911 0.805 13 17 21 +29 11 19 2228 I VF 111.3". *Then:* write the facts about the dataset (it has measurements of redshift; it covers 18 distant galaxy clusters), but no ground truth triple per cell ("RDCSJ 1317+2911" has redshift "0.805"): the values are the dataset's own data, not facts about it.

## Writing a classed triple

1. **[Subject instance](../docs/terminology.md#2-triples) and [object instance](../docs/terminology.md#2-triples): the record's own words, as written.** Don't paraphrase them, and don't expand an acronym the record leaves unexpanded.
2. **The subject is what the sentence is about**, which isn't always the title. Where the record states a fact about what its title names, use the title as the subject instance.
3. **The predicate reads from subject to object**, as the [ground truth schema](../docs/terminology.md#3-schemas) defines it (`annotations/ground_truth_schema.txt`, section PREDICATES: "Each entry below reads subject -> object"). "Dataset ACQUIRED_BY Instrument" means the dataset was collected by the instrument, not the other way round.
4. **[Entity classes](../docs/terminology.md#3-schemas) and predicates: the ground truth schema's**, when one fits, so records name the same things the same way. When none fits, coin one: see *Coining an entity class or predicate*, below.
5. **One fact per [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples).** A sentence that states two facts gives two ground truth triples.
6. **Each fact once**, even if the record states it twice or in other words. (Two ground truth triples that are the same [classed triple](../docs/terminology.md#2-triples) in one record stop step 070 until one is deleted: `annotations/README.md`, *What the pipeline checks*.)
7. **[Source text](../docs/terminology.md#1-records-and-their-text): the shortest passage that states the fact, copied exactly.** Select it in the record's text and press **Use selection**, so it is copied exactly.
8. **A number with a unit: the object instance is the number and its unit, as written.** *Suppose:* a record says "MODIS has a spatial resolution of 250 m." *Then:* the object instance is "250 m", and the predicate says what the number measures (a spatial resolution); coin one if the ground truth schema has none.
9. **A qualifier stays in the instance, as written.** *Suppose:* a record says "The product provides daily snow cover." *Then:* one ground truth triple, with the object instance "daily snow cover". *Suppose instead:* the record says "Data are provided daily." *Then:* that sentence is a fact of its own, and gets its own ground truth triple. The same for a word that describes the data set itself, which can't stay in the subject instance, the title: *Suppose:* a record says "This global data set provides daily snow cover." *Then:* "global" gets its own ground truth triple (HAS_SPATIAL_COVERAGE "global"), and "daily" stays in "daily snow cover".

### Examples

*Two facts in one sentence, and an opinion word.* *Suppose:* a record's text says "The NASA Technical Standards Program provides access to NASA developed standards and handbooks. … The idea is to make it simpler for technical people to access great NASA technical information quickly and conveniently." *Then:* "standards and handbooks" are two things, so two ground truth triples: "NASA Technical Standards Program" (Organization) PROVIDES_ACCESS_TO "NASA developed standards" (Document), and the same with "NASA developed handbooks". The purpose is written without "great". (From `annotations/ground_truth/batch_000.csv`, record `3122be4c-b9d0-4cc9-b6d3-9b96c6e743da`.)

*The subject isn't always the title.* *Suppose:* a record titled "ROSETTA-ORBITER 67P RSI 1/2/3 COMET ESCORT 4 1149 V1.0" says "This is a Rosetta Radio Science data set, collected during the COMET ESCORT 4 phase 2015-10-22 to 2015-12-31." *Then:* the facts about the data set have the title as their [subject instance](../docs/terminology.md#2-triples): … FROM_MISSION "Rosetta" (Mission), … HAS_DISCIPLINE "Radio Science" (Discipline), … HAS_MISSION_PHASE "COMET ESCORT 4 phase" (MissionPhase). But the dates belong to the phase, not to the data set: "COMET ESCORT 4 phase" (MissionPhase) HAS_TIME_SPAN "2015-10-22 to 2015-12-31" (TimeSpan). (From `annotations/ground_truth/batch_000.csv`, record `cfd6ec3f-1e63-4a77-bc3f-007d45f7e2fc`.)

## The describes triple

Every record has one [classed triple](../docs/terminology.md#2-triples) that no text states, written by code: the record's id DESCRIBES its title. Your only part in it is its [entity class](../docs/terminology.md#3-schemas), the [describes class](../docs/terminology.md#2-triples): the entity class of the thing the title names (e.g. Dataset, WebTool). Choose it in the tool's field *Object's entity class* of the [describes triple](../docs/terminology.md#2-triples). `X` means none is chosen yet.

## Coining an entity class or predicate

- **Coin one only when none of the [ground truth schema](../docs/terminology.md#3-schemas)'s fits.** Check the tool's list as you type, and **Help → Ground truth schema** (in the record's strip), which shows every one at a glance: a near-synonym may already exist.
- **Name it in the schema's style:** an [entity class](../docs/terminology.md#3-schemas) in CamelCase (`SpaceMission`), a predicate in UPPER_SNAKE_CASE (`PART_OF_MISSION`), one word each.
- **Give it a one-line definition at once:** press the button under its ✖, in the tool. Until then the model sees it without a definition, the tool marks it ✖, and step 070 won't evaluate a [finished record](../docs/terminology.md#4-ground-truth-and-samples) that uses it.
- **To rename one, or merge two that mean the same thing:** the tool's **Help → Ground truth schema**, then **Edit definitions, rename, or merge…**, then **Rename or merge…** (`annotations/README.md`, *The ground truth schema*).

## Finishing a record

- **Tick *All facts extracted*** only when every fact the record states is there. Only [finished records](../docs/terminology.md#4-ground-truth-and-samples) are extracted (step 060) and evaluated (step 070).
- **A record that states no facts:** delete every [ground truth triple](../docs/terminology.md#4-ground-truth-and-samples) of the record; the tool then keeps one row of the file with only the record's id, which means "annotated, states no facts". Still tick *All facts extracted*.
- **Fix what the tool marks:** ✖ must be fixed (e.g. a [source text](../docs/terminology.md#1-records-and-their-text) that isn't in the record's text); ⚑ is worth a look (e.g. a [subject instance](../docs/terminology.md#2-triples) that isn't in the text, which may be a typo or a deliberate rewording).
- **Commit the file to Git** (`annotations/ground_truth/batch_<NNN>.csv`).
