# Evaluation metrics

The one place each of evaluation's numbers is explained: what it is, its formula with an example, how to read it, what it assumes, and where it comes from. Other files point here instead of repeating it. Terms: [docs/terminology.md](../docs/terminology.md).

## Pairs: what every metric counts

**What.** Record by record, evaluation compares the triples extraction kept with the ground truth triples, after translating extraction's names into the ground truth vocabulary (through `annotations/name_mapping.csv`). A **pair** is one extracted triple and one ground truth triple that state the same fact. Each triple has at most one partner, and evaluation finds the largest possible set of pairs.

| Kind | Rule |
|---|---|
| **exact pair** | Same predicate; same subject instance and same object instance, ignoring case, spacing, quote marks, dashes, punctuation at either end and a leading "a", "an" or "the". |
| **partial pair** | Same predicate; the two subject instances are equal or one appears inside the other as whole words (either way round), and the same holds for the two object instances. Formed only among triples left without an exact partner. |
| **strict pair** | An exact or partial pair whose subject classes and object classes are also the same. |
| **extracted only** | An extracted triple left without a partner. |
| **ground truth only** | A ground truth triple left without a partner: a missed fact. |

**Example.** Ground truth: `MODIS (Instrument) ABOARD Aqua (Spacecraft)`.

- Extracted `the MODIS (Instrument) ABOARD Aqua (Spacecraft)`: exact pair ("the" is ignored), and strict.
- Extracted `Moderate Resolution Imaging Spectroradiometer (MODIS) (Instrument) ABOARD Aqua (Spacecraft)`: partial pair ("MODIS" is inside the subject), and strict.
- Extracted `MODIS (Dataset) ABOARD Aqua (Spacecraft)`: exact pair, not strict (wrong subject class).

**Assumes and can't see.**

- Containment can be fooled: "MODIS" is inside "MODIS Terra", a different instrument. On tuning records you review partial pairs in the annotation tool (*Partial pairs*); two triples marked "not the same fact" are never paired. Held-out records' partial pairs are never reviewed (that would mean looking at them).
- Two names of the current schema that translate to one ground truth name can't be told apart.

**Where from.**

- *Exact* and *partial*: the WebNLG 2020 challenge's evaluation of text-to-triples extraction (Castro Ferreira et al., 2020, [paper](https://aclanthology.org/2020.webnlg-1.7.pdf)). Ours is stricter on partial: whole words, not any overlap.
- *Strict*, meaning right relation and right entity types: the "Strict" setting of end-to-end relation extraction (Bekoulis et al., 2018, as described by Taillé et al., 2020, [paper](https://aclanthology.org/2020.emnlp-main.301/)). WebNLG's "strict" means something else (the element's role must match), so it isn't the source here.
- At most one partner per triple, largest set of pairs: a maximum matching (Kuhn's algorithm, `070_evaluate/070_evaluate_helpers/pairing.py`).
