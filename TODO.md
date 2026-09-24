# TO-DO

- [ ] **Maintainer count.** The README table says 434 Maintainer nodes, but phase 2 merges maintainer spellings down to 422. Phase 1, once we finish Phase 2, will need to be revisited to use the cleaning script used in Phase 2.
- [ ] **Missing README sections.** I need to add a "Repository structure" section (what each folder and script is) and a "How to reproduce" section (setup, harvest, build the graph)
- [ ] **Make a script that extracts facts based off a particular schema.**
  - [ ] Use texts the schema induction script never saw
- [ ] **Make a script that validates extracted facts for the full run.**
  - [ ] Check each fact exists in the text
  - [ ] Add controlled keywords for entity classes and predicates if they exist. The "Mission" entity class should use: <https://www.nasa.gov/a-to-z-of-nasa-missions/>
- [ ] **Enhance script that induces the schema.**
  - [ ] Purview glossary
  - [ ] Neo4j capabilities
  - [ ] Explore alternatives to Stage 4 synonym merge: similarity grouping, passing canonicals forward between batches, a different approach entirely...
  - [ ] Explore SMD site's 5 domains
  - [ ] Before trusting the support counts, find out whether those 15 texts are actually 15 distinct texts, by measuring how similar each maintainer's 15 notes are to each other. High similarity means duplication, and their counts are inflated. Low similarity means they're real independent records, and the counts mean what they are intended to be used for.

    If a group comes back highly similar, two options: drop the duplicates and sample replacements from the same maintainer, or keep them but count that maintainer's contribution once instead of twelve times.
  - [ ] Stage 2 accepts junk and nothing filters it, e.g. the extractor produces "dataset" as a bare subject and reads "VNP43D66 is the BSA" as a type statement, accumulating real support for an unhelpful fact. There's no cheap filter currently, like a stoplist for generic subjects which would cost nothing and remove a known noise source.
- [ ] **Catalog cleaning.**
  - [ ] Enforce DCAT 3.0
