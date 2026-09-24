# data.nasa.gov Knowledge Graph

Fall 2026 Pathways internship project: building a knowledge graph (KG) for [data.nasa.gov](https://data.nasa.gov).

## Records and fields

Throughout this project, a "record" is the metadata of one catalog entry in <[data.nasa.gov](https://data.nasa.gov)>. In JSON terms, each record is one object with 31 possible top-level key-value pairs, of which 24 are populated at least once across the catalog (title, description, maintainer, tags, and so on; the other 7 are empty on every record). Being metadata, the records describe the catalog entries; any actual scientific data or content lives in separate NASA data archives that each record links to, and is never downloaded here. Most catalog entries of data.nasa.gov are datasets.
The keys of these top-level key-value pairs are what we call metadata fields or just fields. Fields come from the raw JSON in which data.nasa.gov's public API returns each record. The API returns every record with the same metadata form provided by CKAN, a standard open-source catalog software, which data.nasa.gov runs on. The data.nasa.gov website renders each record as a readable page (headline, description text, tag buttons), but the harvest in this project comes from the API, which is why we know each the exact name (top-level key) and its exact associated populated content (associated value of the top-level key) of each field for a record, rather than guessing either from webpage text.

An example of a real record can be seen by opening the following link in a browser (ticking off the pretty-print box at the top is advised):<https://data.nasa.gov/api/3/action/package_search?rows=1>. You can see field names that exist in every record, like `id`, `title`, `notes`, `maintainer`, `organization`, `tags`, `resources`, `extras`, etc., as well as the populated contents of each field, which are particular to this record. Several fields hold nested objects and arrays that have fields of their own: `organization` is an object with ~7 inner keys, `tags` is an array where each of its entries has ~4 inner keys, `resources` is an array where each of its entries has ~15 inner keys, and `extras` is a (currently unexplored!) array of extra key-value pairs. Our census counted at the top level, then reached one level deeper only where the design needed it (`tags[].name`, `resources[].format`, `organization.title`). The inner-key counts are approximate because we never censused the nested layers, only the three aforementioned inner keys the design actually reads.

**A note on timing:** the catalog itself is not static! A handful of records is added every week, so any harvest is a snapshot of a specific date. The phase 1 graph was built from a harvest taken 2026-08-30 (36,289 records); a re-harvest on 2026-09-02 returned 36,323. We take care to note the date on which a harvest was taken whenever counts are involved in this README.

## Project phases

There are two phases to the building of this knowledge graph. Phase 1 turned the structured fields, such as `maintainer`, of every record into a fact; phase 2, still in progress, extracts additional facts from the fields involving free-text descriptions such as `title` (title of catalog entry) and `notes` (explanation of catalog entry). Phase 1 is mostly complete, and its schema is summarized in the table below:

| Node label | Count | From | Properties | Relationship to Dataset |
|---|---:|---|---|---|
| Dataset | 36,289 | one per record | id, name, title, created, modified, license | |
| Maintainer | 434 | `maintainer` field | name | `(Dataset)-[:MAINTAINED_BY]->(Maintainer)` |
| Keyword | 8,277 | `tags`, cleaned | name | `(Dataset)-[:TAGGED_WITH]->(Keyword)` |
| Format | 63 | `resources[].format` | name | `(Dataset)-[:AVAILABLE_AS]->(Format)` |

A schema...EDIT
## Phase 1: how the census decided the design

A data census (nasa_census.py) is what decided this design. This script counted, for every field, how often it is filled and how many distinct values it holds. Those counts decided whether and what each field becomes in the knowledge graph:

- If many records share a field's values and those values are worth traversing through, the values become nodes. If a field fails that test but its values still answer some question by filtering or identifying (license, title, dates), the values become properties.
- If a field's values answer no question anyone would ask the graph (`creator_user_id`, `isopen`), the field is ignored.
- Values that mean "empty" become nothing, whatever their field.

These decisions work because of convergence, meaning many different records mentioning the same value. When a value converges, such as 6,214 records sharing the maintainer "Planetary Data System", storing it as one node attaches all 6,214 relationships to it, and standing on that node answers "everything connected to this value" in one hop. A value only one record mentions would yield a node with a single relationship, connecting nothing to nothing, so non-converging values stay properties.

This node-versus-property criterion is standard in property-graph design. The criterion also involves judgment, not just counting: `license_title` has only 4 distinct values shared across thousands of records, but nobody would traverse from license to license, only filter by it, so per the first bullet it stays a property.

Each field's numbers then forced a decision:

- `organization` has 1 distinct value across all records ("NASA"), which connects everything to everything and therefore means nothing, so it is ignored.
- `maintainer` has 435 distinct values that are heavily shared, so it became the `Maintainer` label and the `MAINTAINED_BY` relationship type. Its value "undefined" (989 records) means empty and produces no relationship.
- `tags` has 8,279 distinct values with 132k total uses, so it became the `Keyword` label and `TAGGED_WITH`. Its junk values "__" (7,673 uses) and "nasa" (1,086 uses) produce no nodes.
- `resources[].format` has 63 distinct, heavily shared values, so it became the `Format` label and `AVAILABLE_AS`. Resources exist on only 54.9% of records, so a dataset with no formats is normal, not an error.
- `license_title` has only 4 distinct values. You would filter on it, never traverse through it, so it stays a property on `Dataset`.
- `id`, `name`, `title`, and the timestamps are unique per record, so they stay properties on `Dataset`.
- `notes` is 100% filled with a median of 529 characters of prose, which code cannot parse, so it is reserved for phase 2.
- The remaining administrative fields (`creator_user_id`, `isopen`, `state`, `owner_org`, `private`, `type`, `tracking_summary`, and similar) are populated but answer no question anyone would ask the graph, so they are ignored.
- `extras` is not ignored but deferred: it holds a grab-bag of additional key-value pairs (a look at one record showed entries like publisher and time coverage), and we might explore it further down the line.
- 7 fields (`author`, `author_email`, `groups`, `relationships_as_subject`, `relationships_as_object`, `url`, `version`) exist on every record but are populated on none, so there is nothing to decide about them.

Only three nested fields got a deeper look: `tags[].name`, `resources[].format`, and `organization.title`. Digging into a nested field only pays off if it might contain values shared across records, since only shared values can become nodes, and these three are the only nested fields where that is possible. The other nested fields hold view counts (unique numbers per record) or are empty on every record, and `extras` was consciously deferred, as noted above. Within each of the three, we read the one inner key that names the thing (`name`, `format`, `title`) and skipped the keys that administer it (ids, states, sizes, timestamps).

Phase 1 collected the triples that can be read directly from the structured fields: no interpretation is needed, code just copies each field value into its triple. Phase 2 extracts triples from the natural-language prose in each record's `notes` field, which requires actually reading the text, so a language model does the reading and our code checks its output.

## Phase 2: extracting facts from text (work in progress)

> Phase 2 is not part of the polished deliverable yet.

Phase 2 mines the free-text `notes` and `title` fields of each record, which is where the interesting facts hide: which instrument took the data, aboard which spacecraft, observing what, measuring what.

Where phase 1 merely copied field values into triples, phase 2 has to extract facts from prose, so the work splits into three questions: what vocabulary (schema) should the triples use, how do we get the triples out, and how do we know whether they are right.

### Cleaning

The `notes` and `title` fields are cleaned before anything reads them. About 6% of records carry HTML markup baked into the text (escaped tags, sometimes escaped twice), which would otherwise produce triples about paragraph tags rather than about datasets. The cleaner verifies its own work: every word, number and URL fragment in the source must survive into the cleaned value, and a value that would lose content falls back to a cruder method or to the source text itself. Across the catalog we harvested on 2026-08-30, two values of 36,323 needed a fallback and none lost content. The cleaned title and notes are written to `inputs.json` as one labelled block per record, keyed by the record id.

The same step also joins maintainer spellings, e.g. "Kristan Morgan" and "KRISTAN MORGAN" are one person; left apart they count as two communities everywhere downstream. Names matching once case, punctuation, word order and titles (Dr., Ph.D.) are ignored are treated as one, which merged 10 maintainers and took the count from 435 to 422. Names differing by a middle initial are left apart, since merging those needs a rule nobody has chosen.

### Schema induction

The schema is derived from the catalog rather than written in advance. The data-driven method to induce the schema follows AutoSchemaKG ([arXiv:2505.23628](https://arxiv.org/abs/2505.23628)): take a sample of records (stratified by maintainer), extract facts with no schema imposed, give every extracted name a general label, merge the labels that mean one thing, count how many distinct records produced each candidate, and keep what recurs. Support is counted in distinct records and distinct maintainers, so a pattern backed by one maintainer's house style is visible as such rather than passing as a catalog-wide regularity. Everything the model is told to do that code can re-check afterwards is re-checked: the support arithmetic, the pattern endpoints, and whether quoted examples are real names.

### Evaluation: an annotated pool

None of the above says whether extraction is correct, and no query built on the graph is worth more than the extraction under it. Assessing quality needs ground-truth triples. So a fixed pool of 1,000 records was drawn, once, to be annotated by hand.

The pool is a stratified random sample: records are grouped by maintainer, each group gets places in proportion to its size, maintainers too small to earn two places are combined into one group, and the rows are shuffled so that the first k of them are a fair sample for any k. That last property is what makes partial annotation usable: annotation will stop long before 1,000, and wherever it stops, what has been annotated is still a fair sample rather than one biased by alphabetical or by-maintainer ordering.

Annotating is slow, and the rules had to be worked out on the records themselves. Each record gets one structural row, keeping the catalog entry separate from the thing it describes. The classes and predicates decided this way are kept in a schema file that grows as annotation proceeds; it is small and elementary, and it is expected to keep growing.

Writing every triple by hand is the bottleneck, so a drafting step proposes triples for each record and a person corrects them. The draft is not ground truth: a human keeps, edits, deletes or adds, driven by the record's text. With enough annotated records, extraction can be scored: recall is how many of the hand-written facts the extractor found, and precision is how many of its answers were right. The point of the exercise is not a single number but a fixed measuring stick: the same annotated records can be run against a different prompt, a different model, or extraction with and without the induced schema, and the difference between those runs is what says whether any of them is worth its cost.
