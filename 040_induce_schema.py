"""
040 · Induce schema

Learns the schema from the catalog itself: its entity classes (e.g.
Instrument), predicates (e.g. ABOARD) and patterns (e.g. Instrument ABOARD
Spacecraft). A model reads a sample of texts and lists the triple instances
they state, with no schema imposed; code keeps only those it can verify in
the text; the model gives every component instance a label and merges labels
that mean the same thing; code counts how many texts and maintainers back
each schema entry, and keeps them all with that evidence. Terms:
docs/terminology.md.

Reads:   records.jsonl (020), splits.json (030), and, to compare with,
         annotations/schema_derived_from_manual_annotation.txt
Writes:  the_schema.json, induction_evidence.json
Details: instructions/040_induce_schema.md
"""
from common.step import run_step, helpers

INPUTS = {
    "records":     "020_clean/records.jsonl",
    "splits":      "030_split/splits.json",
    "hand_schema": "./annotations/schema_derived_from_manual_annotation.txt",
}

SETTINGS = {
    "induction_maintainers": 10,    # learn from this many of the largest maintainers
    "texts_per_maintainer":  15,    # the first this-many induction candidates of each
    "min_support":           1,     # a schema entry enters the schema if found in at least this many texts
    "max_chars":             8000,  # a longer text is split into pieces, one call each
    "workers":               4,     # model calls made at the same time
    "confirm_paid_calls":    True,  # stop and ask before the first model call; false for unattended runs
}

induce = helpers("040_induce_schema")


def main(inputs, settings, output):
    texts   = induce.pick_texts(inputs, settings)                  # the first 15 candidates of the 10 largest maintainers
    calls   = induce.paid_calls(settings, output)                  # asks before paying; keeps every answer in cache/
    triples = induce.extract_triple_instances(texts, calls, settings)  # LLM: "MODIS" – "is aboard" – "Aqua", checked in the text
    labels  = induce.label_component_instances(triples, calls)     # LLM, reusing labels chosen so far: "MODIS" → Instrument
    labels  = induce.merge_labels(labels, triples, calls)          # LLM, one call over all labels: Sensor = Instrument
    counts  = induce.count_support(triples, labels)                # code: the texts and maintainers behind each schema entry
    words   = induce.write_definitions(counts, settings, calls)    # LLM: one sentence per entity class and predicate
    schema  = induce.check_schema(counts, words, settings)         # code: what enters the schema, what's deferred
    beside  = induce.compare_with_hand_schema(inputs, schema)      # code: in both / only yours / only induced
    return induce.results(texts, triples, labels, counts, words, schema, beside, calls, settings, output)


if __name__ == "__main__":
    run_step("040_induce_schema", INPUTS, SETTINGS, main)
