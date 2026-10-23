# The pipeline in pictures

The pipeline at a glance, in six diagrams. Each says what it shows in a sentence or two and links to where the details are; the details aren't repeated here. Terms are defined in [`terminology.md`](terminology.md).

## 1. The steps

Eight steps, run in order: `py run_pipeline.py` runs them all (README, *Pipeline overview*), and each also runs on its own, `py <step>/run.py`. Three of them ask a model; in two of them a person has work to do.

```mermaid
---
config:
  look: handDrawn
  handDrawnSeed: 3
  theme: base
  themeVariables:
    fontFamily: '"Segoe Print", "Bradley Hand", "Chalkboard SE", "Comic Sans MS", cursive'
    fontSize: 15px
    primaryColor: "#fffdf8"
    primaryTextColor: "#3b3128"
    primaryBorderColor: "#6e5b49"
    lineColor: "#8a7560"
    textColor: "#3b3128"
    clusterBkg: "#efe8d8"
    clusterBorder: "#a8957f"
    edgeLabelBackground: "#f8f4ea"
  themeCSS: ".rough-node g:first-child path:first-child { stroke-width: 3px; }"
---
flowchart LR
    API[(data.nasa.gov)] --> S010["010 harvest"]
    S010 --> S020["020 clean"]
    S020 --> S030["030 split"]
    S030 --> S040["040 induce schema"]
    S040 --> S050["050 annotate"]
    S050 --> S060["060 extract"]
    S060 --> S070["070 evaluate"]
    S070 --> S080["080 build graph"]
    P1(["a person corrects the drafted batches"]) -.- S050
    P2(["a person checks the translation table"]) -.- S070

    classDef model fill:#f1dc9a,stroke:#8a6a2a
    classDef notbuilt stroke-dasharray: 5 5
    class S040,S050,S060 model
    class S080 notbuilt
```

Yellow: the step asks a model (040 learns the induced schema, 050 drafts classed triples for the ground truth, 060 extracts). 070 asks a model only to propose new rows of the translation table. Dashed: not built yet. What each step does, reads, and writes: the table in the README's *Pipeline overview*, and each step's guide, `<step>/<step>.md`.

## 2. What each step reads

A step reads what earlier steps wrote in `outputs/intermediate_results/`, plus files people keep in `annotations/`, and writes only its own folder. One exception: 070 adds rows to two files in `annotations/` (the translation table, and the log of looks at the held-out part).

```mermaid
---
config:
  look: handDrawn
  handDrawnSeed: 3
  theme: base
  themeVariables:
    fontFamily: '"Segoe Print", "Bradley Hand", "Chalkboard SE", "Comic Sans MS", cursive'
    fontSize: 15px
    primaryColor: "#fffdf8"
    primaryTextColor: "#3b3128"
    primaryBorderColor: "#6e5b49"
    lineColor: "#8a7560"
    textColor: "#3b3128"
    clusterBkg: "#efe8d8"
    clusterBorder: "#a8957f"
    edgeLabelBackground: "#f8f4ea"
  themeCSS: ".rough-node g:first-child path:first-child { stroke-width: 3px; }"
---
flowchart LR
    subgraph steps["the steps (outputs/intermediate_results/)"]
        direction TB
        S010["010 harvest"] --> S020["020 clean"]
        S020 --> S030["030 split"]
        S030 -->|"induction candidates"| S040["040 induce schema"]
        S030 -->|"the pool, in order"| S050["050 annotate"]
        S040 -->|"the_schema.json"| S060["060 extract"]
        S060 -->|"extracted_triples.csv"| S070["070 evaluate"]
        S060 --> S080["080 build graph"]
    end
    subgraph ann["annotations/ (people's files, in Git)"]
        direction TB
        POOL[/"ground_truth_candidates.csv<br/>the ground truth candidates pool"/]
        GTS[/"ground_truth_schema.txt<br/>the ground truth schema"/]
        GT[/"ground_truth/<br/>the ground truth"/]
        ADD[/"schema_additions.txt"/]
        MAP[/"component_class_mapping.csv<br/>the translation table"/]
        REV[/"partial_pair_reviews.csv"/]
    end
    POOL --> S030
    GTS --> S040 & S050 & S070
    S050 -->|"drafted batches, corrected<br/>in the annotation tool"| GT
    GT --> S060 & S070
    ADD --> S060
    MAP <--> S070
    REV --> S070
```

The induction candidates and the pool never share a record, so the schema is never learned from a text it is later evaluated on (README, *Splitting (step 030): two samples that never overlap*). Every step also reads `records.jsonl` (020); the arrows show it only where it's the main input. The files in `annotations/`: the table at the top of `annotations/README.md`.

## 3. The annotation loop

How the ground truth is made and used, and where a person comes in (in the annotation tool, `py helpers/annotate.py`).

```mermaid
---
config:
  look: handDrawn
  handDrawnSeed: 3
  theme: base
  themeVariables:
    fontFamily: '"Segoe Print", "Bradley Hand", "Chalkboard SE", "Comic Sans MS", cursive'
    fontSize: 15px
    primaryColor: "#fffdf8"
    primaryTextColor: "#3b3128"
    primaryBorderColor: "#6e5b49"
    lineColor: "#8a7560"
    textColor: "#3b3128"
    clusterBkg: "#efe8d8"
    clusterBorder: "#a8957f"
    edgeLabelBackground: "#f8f4ea"
  themeCSS: ".rough-node g:first-child path:first-child { stroke-width: 3px; }"
---
flowchart TD
    D["050 drafts the next drafted batch"] --> C["You correct it: Ground truth"]
    C -->|"a coined entity class or predicate"| GS["You add it to the ground truth schema,<br/>with a one-line definition"]
    GS --> C
    C -->|"commit annotations/ to Git"| E["060 extracts the finished records"]
    E --> V["070 evaluate"]
    V -->|"new rows"| T["You check them: Translation table"]
    T --> V
    V -->|"partial pairs"| R["You review them: Partial pairs"]
    R --> V
    V --> N["The numbers: outputs/reports/070_evaluate_…md"]
```

Each box where you act is a view of the annotation tool; what each view does: `annotations/README.md`. What to write in the ground truth: [`annotations/guidelines.md`](../annotations/guidelines.md).

## 4. Inside evaluation

How 070 compares one record's extracted triples with its ground truth triples (in full: [`070_evaluate/metrics/pairs.md`](../070_evaluate/metrics/pairs.md)).

```mermaid
---
config:
  look: handDrawn
  handDrawnSeed: 3
  theme: base
  themeVariables:
    fontFamily: '"Segoe Print", "Bradley Hand", "Chalkboard SE", "Comic Sans MS", cursive'
    fontSize: 15px
    primaryColor: "#fffdf8"
    primaryTextColor: "#3b3128"
    primaryBorderColor: "#6e5b49"
    lineColor: "#8a7560"
    textColor: "#3b3128"
    clusterBkg: "#efe8d8"
    clusterBorder: "#a8957f"
    edgeLabelBackground: "#f8f4ea"
  themeCSS: ".rough-node g:first-child path:first-child { stroke-width: 3px; }"
---
flowchart LR
    X["extracted triple<br/>(the current schema's component classes)"] -->|"translation table"| TX["translated extracted triple<br/>(the ground truth schema's component classes)"]
    G["ground truth triple"] --> PAIR{"pairs<br/>exact, then partial"}
    TX --> PAIR
    PAIR -->|"each occurrence<br/>in a pair is correct"| PREC["precision"]
    PAIR -->|"each ground truth triple<br/>in a pair is found"| REC["recall"]
```

Each occurrence (of a translated extracted triple) pairs with at most one ground truth triple of the same record, and the other way round. Exact and partial are the two pair levels. Every number comes with its margin of error: [`070_evaluate/metrics.md`](../070_evaluate/metrics.md).

## 5. Tracing an output

What every run leaves behind, so that any output can be traced back to where it came from ([`helpers/audit.md`](../helpers/audit.md)).

```mermaid
---
config:
  look: handDrawn
  handDrawnSeed: 3
  theme: base
  themeVariables:
    fontFamily: '"Segoe Print", "Bradley Hand", "Chalkboard SE", "Comic Sans MS", cursive'
    fontSize: 15px
    primaryColor: "#fffdf8"
    primaryTextColor: "#3b3128"
    primaryBorderColor: "#6e5b49"
    lineColor: "#8a7560"
    textColor: "#3b3128"
    clusterBkg: "#efe8d8"
    clusterBorder: "#a8957f"
    edgeLabelBackground: "#f8f4ea"
  themeCSS: ".rough-node g:first-child path:first-child { stroke-width: 3px; }"
---
flowchart TD
    subgraph run["One run, e.g. 020_clean_2026-10-12_1030"]
        R["report<br/>outputs/reports/#lt;run id#gt;.md"]
        L["log<br/>outputs/logs/#lt;run id#gt;.log"]
        M["_manifest.json<br/>files in and out, with hashes"]
        O["_origin, inside each output item<br/>the input item(s) it was made from"]
    end
    O -->|"file and item"| U["010's batch file and its record"]
    U -->|"the request that fetched it"| API[(data.nasa.gov)]
    M -->|"which run made each input"| U
    PR["previous_runs/#lt;run id#gt;/<br/>the earlier version of each file a run changed"] -.- run
```

`py helpers/audit.py <record id>` follows the origins back, step by step. Measured results that rest on these runs: [`findings.md`](findings.md).

## 6. The folders

```
010_harvest/ … 080_build_graph/   one folder per step: run.py (its control panel), its guide, its code
common/                           code that more than one step uses
helpers/                          tools that aren't steps: the annotation tool, audit, run comparison, models
annotations/                      what people make and keep in Git: the ground truth and its files
docs/                             terminology, findings, improvements, this page
tests/                            the tests
outputs/                          everything a run makes (not in Git): results, reports, logs, caches
run_pipeline.py                   every step, in order
```

Every file and folder, with where each is explained: the README, *What's in this repository*.
