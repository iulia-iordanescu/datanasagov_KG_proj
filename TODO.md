# TO-DO

- [ ] **Missing README sections.** I need to add a "Repository structure" section (what each folder and script is) and a "How to reproduce" section (setup, harvest, build the graph)
  - [x] Repository structure (done: README, "What's in this repository")
  - [ ] How to reproduce (setup and running the steps: `docs/running_on_nasa_laptop.md`; building the graph: not yet, step 080)
- [x] **Make a script that extracts facts based off a particular schema.** (done: step 060)
  - [x] Use texts the schema induction script never saw (done: by default 060 extracts from the finished ground truth records, which 030 keeps apart from 040's texts)
- [ ] **Make a script that validates extracted facts for the full run.**
  - [x] Check each fact exists in the text (done: `common/validate.py`, used by 040, 050, 060 and the annotation tool)
  - [ ] Add controlled keywords for entity classes and predicates if they exist. The "Mission" entity class should use: <https://www.nasa.gov/a-to-z-of-nasa-missions/>
- [x] **Make a script that drafts the ground truth triples.** (done: step 050, corrected with `py annotate.py`)
  - [x] Use texts the schema induction script never saw; draw the pool of records that can be used potentially ONCE so that you don't have to worry about this ever again.
- [x] **Make a script that compares ground truth triples to found triples for a set of texts via precision and recall.** (done: step 070)
  - [ ] Explore and research other quality metrics, e.g. coverage and partial accuracy (partly done: 070 also reports partial matches, entity-class accuracy and the schema ceiling)
- [ ] **Enhance script that induces the schema.**
  - [ ] Purview glossary
  - [ ] Neo4j capabilities
  - [ ] Explore alternatives to Stage 4 synonym merge: similarity grouping, passing canonicals forward between batches, a different approach entirely...
  - [ ] Explore SMD site's 5 domains
  - [ ] Before trusting the support counts, find out whether those 15 texts are actually 15 distinct texts, by measuring how similar each maintainer's 15 notes are to each other. High similarity means duplication, and their counts are inflated. Low similarity means they're real independent records, and the counts mean what they are intended to be used for.

    If a group comes back highly similar, two options: drop the duplicates and sample replacements from the same maintainer, or keep them but count that maintainer's contribution once instead of fifteen times.
  - [ ] Stage 2 accepts junk and nothing filters it, e.g. the extractor produces "dataset" as a bare subject and reads "VNP43D66 is the BSA" as a type statement, accumulating real support for an unhelpful fact. There's no cheap filter currently, like a stoplist for generic subjects which would cost nothing and remove a known noise source.
  - [x] (done: steps 050 and 060 write it for every record, `common/triples_io.py`) We should enforce the following in our schema. Every record gets one structural triple that keeps a catalog entry separate from the thing it describes. The only piece code does not handle, i.e. the LLM's role, is deciding what type of thing the record is describing (a dataset, a publication, etc):
       <record id> (CatalogEntry) DESCRIBES <title> (its class)
  - [ ] Consider properties, since we are moving in the direction of an LPG
  - [ ] Explore data.nasa.gov public-facing website for inspiration about entity classes to include and predicates, e.g. the filters a user can apply for a search
  - [ ] It's possible other fields (free-text description or structured alike) might be useful to include as the text by which schema is induced...so far, we've used just `title` and `notes`
  - [x] Break it apart into separate scripts, each handling its own job in the schema induction process. It'll be much easier to debug. (done: step 040, one file per stage)

- [ ] **Catalog cleaning.**
  - [ ] Enforce DCAT 3.0
  - [ ] The README table says 434 Maintainer nodes, but phase 2 merges maintainer spellings down to 422. Phase 1, once we finish Phase 2, will need to be revisited to use the cleaning script used in Phase 2.
- [ ] **Return to Phase 1.**
  - [ ] Deeper dive into other existing metadata fields to yield more "trivial triples" (triples that come from structured metadata fields)...these might become properties!
- [x] (done: step 020 writes `records.jsonl` with each field under its own key) **!!! Sections in inputs.json are guessed from labels.** Each record's text is one string of "label: value" paragraphs, so scripts find a section by a paragraph starting with "<label>:". A paragraph inside notes that happens to start with another section's label (e.g. "author:") is mistaken for that section. Fix in build_inputs.py: store each section under its own key instead of one labelled string, then update every script that reads inputs.json. Only matters once sections beyond title and notes are added.
