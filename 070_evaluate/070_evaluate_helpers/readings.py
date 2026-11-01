"""
readings.py -- each metric read as plain sentences, with the run's own
numbers in them, for the report (see the guide's section *Reading the
metrics*).

A metric is a ratio; these bullets say what it counts, in this run's terms:
what the classed triples are and where they came from (once per part, in "Where
these numbers come from"), then, per metric, the counts behind it, how to
read it as a chance and for the knowledge graph where that holds, how sure
it is (the margin of error, or why there is none), and what it assumes. A
metric gets only the readings that hold for it.
"""
from __future__ import annotations

import collections
import re

import stats
from component_classes import IDENTITY
from common.ground_truth import HELD_OUT, TUNING
from common.triples_io import component_class_key


#: How every number of the report, per_record.md and the readings is written when its formula would divide by 0: one
#: spelling everywhere (a reason that varies follows it, after a colon, inside the brackets).
NO_VALUE = "no value (0 to divide by)"


def pct(x) -> str:
    """A proportion as a whole percentage: "50%", or NO_VALUE for none."""
    return NO_VALUE if x is None else f"{100 * x:.0f}%"


def _of(k: int, n: int) -> str:
    """k, with its proportion of n: "4 (50%)" (the sentence names n)."""
    return f"{k} ({pct(k / n) if n else NO_VALUE})"


#: The caveat after a range from fewer than stats.FEW_RECORDS records (070_evaluate/metrics/approximately.md).
FEW_CAVEAT = ("From {n} records only: the design effect (how much the records' occurrences move together) is itself "
              "estimated from {n} records, so the range may still be too narrow; read it as a rough width, not a bound.")


def _sure(n: dict, metric: dict, what: str, items: str = "triples") -> str:
    """How sure a metric is: its margin of error (stats.clustered_wilson), or why there is none."""
    if metric is None or metric.get("value") is None:
        return f"- Not computed: nothing to count it over."
    if metric.get("low") is None:
        return "- Computed over 1 record: no range (nothing to measure spread from)."
    out = (f"- For the whole catalog, {what} is likely between {pct(metric['low'])} and {pct(metric['high'])} "
           f"(the margin of error: a 95% interval over these {n['records']} records' {items}, worth "
           f"{metric['n_eff']:.0f} independent ones once the records' clustering is counted"
           + ("; every one of them agreed, so each record counts as one trial" if metric.get("deff") is None else "")
           + ").")
    return out + (" " + FEW_CAVEAT.format(n=n["records"]) if n["records"] < stats.FEW_RECORDS else "")


#: What a held-out look saw, besides its date and run (columns of annotations/held_out_looks.csv), as a message names
#: it. Two looks can show different held-out numbers only if one of these differs, or the code.
LOOK_INPUTS = {"schema": "the current schema", "extraction_run_id": "060's run (the extracted triples)",
               "translation_sha256": "the translation (the rows of the translation table used)",
               "held_out_ground_truth_sha256": "the held-out records' ground truth",
               "held_out_records": "the number of held-out records evaluated"}


def since_previous(looks: dict) -> str:
    """What changed since the previous held-out look (moves._log_look), as a sentence."""
    if looks["changed"] is None:
        return "This is the first look."
    p = looks["previous"]
    when = f"the previous look ({p.get('date') or 'no date'}, run {p.get('run_id') or 'unknown'})"
    if not looks["changed"]:
        return (f"Since {when}, nothing that sets the held-out numbers changed, except perhaps the code (each run's "
                f"report in outputs/reports/, section *Run*, gives its code version), so they should be the same.")
    return f"Since {when}, changed: {'; '.join(looks['changed'])}."


def held_out_only_note(recs: list, marked: dict) -> str:
    """The held-out part's line on the ground truth triples that use held-out-only entries (docs/terminology.md):
    the current schema can't reach them by design (no row of the translation table may target one), so they count
    against recall, out of reach."""
    keys = {k: {component_class_key(n): n for n in marked.get(k, ())} for k in ("entity_classes", "predicates")}
    used = {"predicates": collections.Counter(), "entity_classes": collections.Counter()}
    G = n_using = 0
    for r in recs:
        for g in r["gt"]:
            G += 1
            p = keys["predicates"].get(component_class_key(g["predicate"]))
            e = [keys["entity_classes"][k] for k in (component_class_key(g["subject_class"]),
                                                     component_class_key(g["object_class"])) if k in keys["entity_classes"]]
            if p:
                used["predicates"][p] += 1
            for x in e:
                used["entity_classes"][x] += 1
            n_using += bool(p or e)
    if not n_using:
        return "- **Held-out-only entries:** no ground truth triple of these records uses one."
    names = lambda c: ", ".join(f"{n} ({k})" for n, k in c.most_common()) or "none"     # noqa: E731
    return (f"- **Held-out-only entries:** {n_using} of the {G} ground truth triples use entries marked held-out only "
            f"(predicates: {names(used['predicates'])}; entity classes: {names(used['entity_classes'])}), which the "
            f"current schema can't reach by design: those with such a predicate count against recall and are out of "
            f"reach; those with such an entity class can never be in a strict pair (`docs/terminology.md`, "
            f"*held-out-only entry*).")


def where_from(part: str, recs: list, evaluated, translation, looks) -> list:
    """Once per part: what these numbers were computed from."""
    made = evaluated.extraction_made
    schema = evaluated.schema_used.get("made", {})
    additions = [e for kind in ("entity_classes", "predicates", "patterns") for e in evaluated.schema_used.get(kind, [])
                 if e.get("from") == "additions"]               # a pattern added alone has its own source
    from_tuning = [e for e in additions if re.search(r"ground[\s_-]*truth", (e.get("source") or "").lower())]
    positions = sorted(r["position"] for r in recs if r.get("position") is not None)
    review = {k: sum(r["compared"]["partial_review"][k] for r in recs) for k in ("unreviewed", "rejected")}
    out = ["#### Where these numbers come from", "",
           f"- **Extracted triples:** from extraction's run `{made.get('run_id', 'unknown: not in the details file of extraction')}` "
           f"(model `{made.get('model', 'unknown')}`), in `060_extract/extracted_triples.csv`.",
           f"- **The current schema (the one extraction used):** `{schema.get('schema', 'unknown')}`, plus "
           f"`{schema.get('additions', 'annotations/schema_additions.txt')}` ({len(additions)} schema entr(ies) from it).",
           ("- **Schema entries of the schema additions learned from tuning records:** "
            + "; ".join(f"{e.get('component_class') or ' '.join(e['pattern'])} ({e.get('source')})" for e in from_tuning) + ". They come from the very records "
            "being evaluated, so they help here more surely than on records the pipeline hasn't seen."
            if from_tuning else "- **Schema entries of the schema additions learned from tuning records:** none."),
           ("- **Component classes:** translation: identity (060 used the ground truth schema): each of extraction's "
            "component classes is itself, the translation table not read. The ground truth schema was shaped while "
            "annotating the tuning records, so these numbers are a reference, not a held-out result."
            if getattr(translation, "how", "") == IDENTITY else
            "- **Component classes:** extraction's component classes translated into the ground truth schema through "
            "`annotations/component_class_mapping.csv`."),
           f"- **Ground truth:** `annotations/ground_truth/`, the {len(recs)} finished {part} record(s) of the fair "
           f"sample (pool positions {', '.join(f'#{p}' for p in positions) or '–'}). Drafted by a model (step 050) and "
           f"corrected by a person, not written from scratch, so recall is likely overstated "
           f"(`070_evaluate/metrics/recall.md`, *Assumes and can't see*).",
           ("- **Partial pairs:** " + (f"{review['unreviewed']} not reviewed yet; pairs your review ruled out (\"not the same "
                                        f"fact\"): {review['rejected']}."
                                        if part == TUNING else
                                        "never reviewed for the held-out part (that would mean looking at it).")),
           ]
    if part == HELD_OUT:
        out.append(held_out_only_note(recs, getattr(evaluated, "held_out_only", None) or {}))
        out.append(f"- **Held-out looks:** the held-out numbers have been shown {looks['count']} time(s), this run "
                   f"included (`annotations/held_out_looks.csv`). {since_previous(looks)} A change made after seeing "
                   f"them lets these records influence the pipeline, so they no longer measure records it was never "
                   f"adjusted to.")
    out += ["- **The full recipe** of each run (code version, settings, prompts with their fingerprints, inputs "
            "and the runs that made them): that run's report in `outputs/reports/`, sections Run, Settings, "
            "Prompts and Inputs.", ""]
    return out


def untranslatable_predicates(recs: list) -> list:
    """[(predicate of the current schema, its untranslatable occurrences)] over records, most occurrences first."""
    found = collections.Counter(t["crt"]["predicate"] for r in recs for t, u in
                                zip(r["compared"]["translated"], r["compared"].get("untranslatable", ())) if u)
    return sorted(found.items(), key=lambda kv: (-kv[1], component_class_key(kv[0])))


def readings(part: str, n: dict, recs: list, evaluated, translation, looks, confusion: dict) -> list:
    E, G = n["extracted"], n["gt_triples"]
    ex, pa = n["exact"], n["partial"]
    # precision's denominators: the occurrences less the untranslatable ones and those paired with a fact that waits on
    # an expert (pairing.py)
    U = n.get("untranslatable", 0)
    T = E - U
    Ee, Ep = ex.get("counted_occurrences", T), pa.get("counted_occurrences", T)
    ex.setdefault("pending_pairs", 0)
    pa.setdefault("pending_pairs", 0)
    out = [f"### Reading the metrics: {part} part", ""] + where_from(part, recs, evaluated, translation, looks)

    # precision
    out += [f"#### Precision: {pct(ex['precision']['value'])} (exact pairs), {pct(pa['precision']['value'])} "
            f"(exact and partial pairs), over the {T} translatable occurrences", "",
            f"- Of the {E} occurrences of these records (one per extracted triple, translated into the ground "
            f"truth schema), {U} are untranslatable (their predicate translates to (none): the ground truth schema "
            f"can't say them, so they are judged neither right nor wrong; section *Schema fit*), leaving {T}; of "
            f"those, {_of(ex['pairs'], Ee)} are correct at the exact level, and {_of(pa['pairs'], Ep)} at "
            f"the partial level"
            + (f", of the {Ee} and {Ep} counted: {ex['pending_pairs']} and {pa['pending_pairs']} match a fact that "
               f"waits on an expert (exact, partial), and are left out of precision (section *Extracted triples "
               f"matching facts that wait on an expert*)." if ex["pending_pairs"] or pa["pending_pairs"] else "."),
            f"- So in a knowledge graph built from the whole catalog's extracted triples, approximately "
            f"{pct(ex['precision']['value']) if E else NO_VALUE} of those edges whose predicate the ground truth "
            f"schema can say would be correct at the exact "
            f"level ({pct(pa['precision']['value']) if E else NO_VALUE} at the partial level): an estimate, since "
            f"precision is measured on the evaluated records only.",
            f"- Partial minus exact: {_of(pa['pairs'] - ex['pairs'], Ep)} of the occurrences form a partial pair: "
            f"correct only at the partial level, where a subject instance or object instance may be inside the "
            f"other's as whole words (e.g. \"MODIS\" inside its full name).",
            f"- Precision minus strict precision: {_of(ex['pairs'] - ex['strict_pairs'], Ee)} of the occurrences "
            f"state the right fact but with a wrong subject class or object class (exact level; "
            f"{_of(pa['pairs'] - pa['strict_pairs'], Ep)} at the partial level).",
            _sure(n, ex["precision"], "exact precision"),
            "- Assumes the ground truth lists every fact these records state: an occurrence stating a true "
            "fact the ground truth lacks counts as not correct.", ""]

    # schema fit
    named = "; ".join(f"`{p}` ({k})" for p, k in untranslatable_predicates(recs)[:5])
    out += [f"#### Schema fit: {pct(n['schema_fit']['value'])}", "",
            f"- (occurrences − untranslatable occurrences) ÷ occurrences = ({E} − {U}) ÷ {E} = "
            f"{pct(n['schema_fit']['value'])}.",
            f"- Of what extraction states, {pct(n['schema_fit']['value'])} is something the ground truth schema can "
            f"say through the checked translation table; the other {U} occurrence(s) are edges a knowledge graph "
            f"would hold that no ground truth triple can confirm or deny. Not a mistake of the model by itself: the "
            f"model extracts with the current schema and never sees the ground truth schema.",
            (f"- The predicates (current schema) of the untranslatable occurrences, most occurrences first: {named}."
             if named else "- No occurrence is untranslatable."),
            _sure(n, n["schema_fit"], "schema fit"),
            "- A wrong `(none)` row of the translation table lowers it and hides an occurrence from precision "
            "(`070_evaluate/metrics/precision.md`, *Untranslatable occurrences*).", ""]

    # recall
    out += [f"#### Recall: {pct(ex['recall']['value'])} (exact pairs), {pct(pa['recall']['value'])} "
            f"(exact and partial pairs)", "",
            f"- Of the {G} ground truth triples, {_of(ex['pairs'], G)} have an exact pair; counting partial pairs "
            f"too, {_of(pa['pairs'], G)}.",
            f"- Read as a chance: a ground truth triple has a {pct(ex['recall']['value'])} chance of being found "
            f"as an exact pair ({pct(pa['recall']['value'])} counting partial pairs).",
            f"- A knowledge graph built from the extracted triples would lack {G - ex['pairs']} of the {G} "
            f"facts ({pct((G - ex['pairs']) / G) if G else NO_VALUE}) these records state, per the ground truth ({G - pa['pairs']} counting partial pairs as found).",
            _sure(n, ex["recall"], "exact recall"),
            "- Assumes the ground truth lists every fact these records state: a fact missing from it is not "
            "counted at all.", ""]

    # F1
    out += [f"#### F1: {pct(ex['f1']['value'])} (exact pairs), {pct(pa['f1']['value'])} (exact and partial pairs)",
            "",
            f"- Precision and recall in one number: 2 × precision × recall ÷ (precision + recall), here "
            f"2 × {ex['pairs']} pairs ÷ ({Ee} occurrences counted (the translatable ones, less those matching a fact "
            f"that waits on an expert) + {G} ground truth triples). It's high only when both are.",
            "- The usual headline number for comparing runs or models, and with published results. It weighs "
            "precision and recall equally; read them too when one matters more (for a knowledge graph, a wrong "
            "edge is often worse than a missing one).",
            _sure(n, ex["f1"], "exact F1"), ""]

    # strict
    out += [f"#### Strict precision and strict recall: {pct(ex['strict_precision']['value'])} and "
            f"{pct(ex['strict_recall']['value'])} (exact pairs)", "",
            f"- The same, counting only strict pairs: pairs whose two entity classes also agree, after translation. "
            f"{ex['strict_pairs']} of the {ex['pairs']} exact pairs are strict ({pa['strict_pairs']} of the "
            f"{pa['pairs']} counting partial pairs).",
            f"- Strict precision: {ex['strict_pairs']} of the {Ee} occurrences counted "
            f"({pct(ex['strict_precision']['value'])}); strict recall: {ex['strict_pairs']} of the {G} ground "
            f"truth triples ({pct(ex['strict_recall']['value'])}).",
            f"- Strict F1: {pct(ex['strict_f1']['value'])} (exact pairs).",
            "- For a knowledge graph: a strict pair is an edge whose two nodes would also get the right "
            "entity classes (node labels).",
            _sure(n, ex["strict_precision"], "exact strict precision"), ""]

    # entity-class accuracy
    shared = [f"{', '.join(v)} (current schema) --> {k} (ground truth schema)"
              for kind in ("entity class",) for k, v in translation.merged.get(kind, {}).items()]
    out += [f"#### Entity-class accuracy: {pct(ex['entity_class_accuracy']['value'])} (exact pairs), "
            f"{pct(pa['entity_class_accuracy']['value'])} (exact and partial pairs)", "",
            f"- Of the {ex['pairs']} exact pairs, {_of(ex['strict_pairs'], ex['pairs'])} also have both entity "
            f"classes right; of the {pa['pairs']} pairs counting partial ones, {_of(pa['strict_pairs'], pa['pairs'])}.",
            f"- Read as a chance: when extraction finds a fact, its subject class and object class are both right with "
            f"a {pct(ex['entity_class_accuracy']['value'])} chance.",
            f"- It is the factor by which requiring the entity classes too lowers precision and recall: strict precision "
            f"= precision × entity-class accuracy, and strict recall = recall × entity-class accuracy, at the same "
            f"pair level (exact: {pct(ex['strict_precision']['value'])} = {pct(ex['precision']['value'])} × "
            f"{pct(ex['entity_class_accuracy']['value'])}).",
            f"- Which entity class goes wrong: of the {ex['pairs']} exact pairs, {_of(ex['subject_class_pairs'], ex['pairs'])} "
            f"have the right subject class (subject-class accuracy) and {_of(ex['object_class_pairs'], ex['pairs'])} the "
            f"right object class (object-class accuracy). Entity-class accuracy needs both, so it is never above either.",
            "- Only pairs are judged: the entity classes of an occurrence left extracted only (wrong, or a "
            "repeat of a fact already paired) aren't counted.",
            _sure(n, ex["entity_class_accuracy"], "exact entity-class accuracy")]
    if shared:
        out.append("- Can't see mix-ups between component classes of the current schema that translate to the same ground truth component class: "
                   + "; ".join(shared) + ".")
    out.append("")

    # recall upper bound and recall within reach
    W, SW = n["within_reach"], n["within_strict_reach"]
    out += [f"#### Recall upper bound: {pct(n['recall_upper_bound']['value'])}; strict: "
            f"{pct(n['strict_recall_upper_bound']['value'])}", "",
            f"- Of the {G} ground truth triples, {_of(W, G)} are within reach: their predicate has a counterpart "
            f"in the current schema, through the translation table. That's all a pair needs, so it's the most "
            f"recall any extraction could get with this schema and translation table: {G - W} ground truth "
            f"triple(s) have a predicate with no counterpart in the schema.",
            f"- {_of(SW, G)} are within strict reach: their two entity classes have a counterpart too. That's "
            f"the most strict recall could be.",
            _sure(n, n["recall_upper_bound"], "the recall upper bound"), ""]
    out += [f"#### Recall within reach: {pct(ex['recall_within_reach']['value'])} (exact pairs), "
            f"{pct(pa['recall_within_reach']['value'])} (exact and partial pairs)", "",
            f"- Of the {W} ground truth triples within reach, {_of(ex['pairs_within_reach'], W)} have an exact "
            f"pair; counting partial pairs too, {_of(pa['pairs_within_reach'], W)}.",
            f"- Strict: of the {SW} within strict reach, {_of(ex['strict_pairs_within_reach'], SW)} have a strict "
            f"exact pair.",
            "- Every pair's ground truth triple is within reach, so recall = recall upper bound × recall within reach "
            f"(exact: {pct(ex['recall']['value'])} = {pct(n['recall_upper_bound']['value'])} × "
            f"{pct(ex['recall_within_reach']['value'])}): the first factor is the schema's part, the second extraction's.",
            "- Read with the recall upper bound: a low upper bound points at the schema; a low recall within reach points "
            "at extraction (its model, prompt or checks), since those ground truth triples could have been found.",
            _sure(n, ex["recall_within_reach"], "exact recall within reach"), ""]

    # describes
    d = n["describes"]
    truths, spelled = collections.Counter(), {}
    for (t, _), k in confusion.items():                # by component class, as stats.numbers groups them
        truths[component_class_key(t)] += k
        spelled.setdefault(component_class_key(t), t)
    common = spelled[truths.most_common(1)[0][0]] if truths else None
    right = round((d["accuracy"]["value"] or 0) * d["records"]) if d["accuracy"]["value"] is not None else 0
    out += [f"#### Describes accuracy: {pct(d['accuracy']['value'])}", "",
            f"- Of the {d['records']} record(s) whose ground truth names a describes class, extraction named "
            f"the same describes class for {_of(right, d['records'])}.",
            (f"- The describes baseline (always naming the most common describes class, `{common}`, ground truth "
             f"schema): {pct(d['majority_baseline'])}. The describes accuracy means something only when it's clearly "
             f"above that. The describes baseline comes from these records' own ground truth, so it has no margin of "
             f"error."
             if common else "- No describes baseline: no record's ground truth names a describes class."),
            f"- The describes per-entity-class average ({len(truths)} describes class(es), each weighing the same): "
            f"{pct(d['per_entity_class_average'])}, so a rare one counts as much as a common one."
            + (f" Always naming `{common}` would get {pct(1 / len(truths))} on it." if truths else "")
            + " No margin of error: a describes class with few records moves it a lot.",
            _sure(n, d["accuracy"], "this accuracy"), ""]
    return out


# --------------------------------------------------------------------------
# One line per row of the report's tables per predicate, per entity class, and per record (070_evaluate.md,
# *Reading each row*, which lists every cause a line can name and the rule that names it). Each line states its
# row, the counts it rests on, and, for each thing that counts against the row, the step(s) that can cause it,
# naming one only where the counts rule the others out.

#: Where the rules of every reading are written; each line ends with it.
RULES = "`070_evaluate/070_evaluate.md`, *Reading each row*"

#: A row (or record) whose occurrences and ground truth triples together number at most this, and that something
#: counts against, is read as too few to say which step caused it. A rule of thumb, with no source: at 2, one more
#: triple would change its percentages by 50 points or more.
TOO_FEW = 2

#: The step or file each cause comes from, as the lines name them.
SCHEMA = "the current schema (by default step 040's induced schema plus the schema additions)"
TABLE = "the translation table (`annotations/component_class_mapping.csv`)"
PAIRS_DEF = "`070_evaluate/metrics/pairs.md`, Definition"
#: Where every cause is listed: the counts never rule all the others out, so a line names the likeliest among them.
RECALL_CAUSES = "`070_evaluate/metrics/recall.md`, *When a ground truth triple counts as not found*"
PRECISION_CAUSES = "`070_evaluate/metrics/precision.md`, *When an occurrence counts as not correct*"
#: The causes of a ground truth triple within reach with no pair that the counts can't tell from extraction's own.
NOT_RULED_OUT = ("step 060 removed the extracted triple for a check, a row of the translation table translates its "
                 "predicate to the wrong one or with the wrong swap_subject_and_object, a near-repeat in the ground "
                 "truth, a \"not the same fact\" verdict, or its occurrence taken by a wrong pair")
MULTISET = "`070_evaluate/metrics/pairs.md`, Example, *A multiset of translated extracted triples*"

#: Per table: the entity class in which a pair that counts for the row can differ (so it isn't strict), and the
#: component classes extraction could have given a ground truth triple of the row instead of its own.
_DIFFER = {"predicate": "subject class or object class", "subject class": "object class",
           "object class": "subject class"}
_OTHER = {"predicate": "another predicate", "subject class": "another predicate or another subject class",
          "object class": "another predicate or another object class"}


def _n(k: int, word: str) -> str:
    """ "1 occurrence", "3 occurrences"."""
    return f"{k} {word}{'' if k == 1 else 's'}"


def _a(word: str) -> str:
    return ("an " if word[0] in "aeiou" else "a ") + word


def _has(k: int) -> str:
    return "has" if k == 1 else "have"


def _are(k: int) -> str:
    return "is" if k == 1 else "are"


def _they(k: int) -> str:
    return "it can't" if k == 1 else "they can't"


def _no_value(x) -> str:
    return pct(x)


def _gap(kind: str) -> str:
    """The cause of a component class (or ground truth triple) out of reach."""
    return (f"either {SCHEMA} has no {kind} with that meaning, or {TABLE} has no checked row translating one of "
            f"the current schema's to it")


def _multiplied(k: int) -> str:
    return (f" {k} of its occurrences have multiplicity > 1: two or more extracted triples of their record "
            f"translate to the same translated extracted triple, and at most one of those copies can pair with a "
            f"given ground truth triple ({MULTISET})." if k else "")


def _too_few(O: int, G: int, what: str) -> str:
    return (f"only {O + G} triple{'' if O + G == 1 else 's'} ({_n(O, 'occurrence')} + {_n(G, 'ground truth triple')}), "
            f"and 070 names a cause only for more than {TOO_FEW} (a rule of thumb, with no source): too few to say "
            f"which step caused {what}.")


def _causes(said: str, causes: list, none: str) -> str:
    """The line: what it rests on, then each cause as a sentence, or what holds when nothing counts against it."""
    return f"{said}. " + (". ".join(c[0].upper() + c[1:] for c in causes) if causes else none) + "."


def _end(s: str) -> str:
    return f"{s} (rules: {RULES})"


def component_class_reading(r: dict, table: str) -> str:
    """One line reading a row of a table per predicate, per subject class, or per object class
    (stats.per_component_class), at the partial level, with its exact pairs alongside."""
    name, O, G, k = r["component_class"], r["occurrences"], r["ground_truth_triples"], r["within_strict_reach"]
    Pe, Pp, Sp = r["exact"]["pairs"], r["partial"]["pairs"], r["partial"]["strict_pairs"]
    many = _multiplied(r["occurrences_multiplicity_above_1"])
    if r["within_reach"] is None:
        if table == "predicate":
            return _end(f"{name}: its row of {TABLE} says (none), so "
                        + (f"its 1 occurrence is" if O == 1 else f"its {O} occurrences are")
                        + f" untranslatable: left out of precision (which has no value here) and counted in schema "
                          f"fit: either {SCHEMA} has {_a(table)} the ground truth schema lacks, "
                          f"or that row should name one of the ground truth schema's." + many)
        return _end(f"{name}: its row of {TABLE} says (none), so "
                    + (f"its 1 occurrence can't" if O == 1 else f"none of its {O} occurrences can")
                    + " be in a pair"
                    + (f" (precision 0%)" if not r.get("untranslatable") else
                       f" ({r['untranslatable']} of them untranslatable, left out of its precision: precision "
                       + ("has no value" if r["untranslatable"] == O else "0%") + ")")
                    + f": either {SCHEMA} has {_a(table)} the ground truth schema lacks, "
                      f"or that row should name one of the ground truth schema's." + many)
    name = f"{name} ({table}, ground truth schema)"
    if r["within_reach"] is False:
        return _end(f"{name}: out of reach: no checked row of {TABLE} translates a {table} of the current schema to "
                    f"it, so none of its {_n(G, 'ground truth triple')} can be in a pair (recall 0%): {_gap(table)}."
                    + many)
    U = r.get("untranslatable", 0)
    Ot = O - U                                  # the occurrences precision counts (untranslatable ones left out)
    against = Ot + G - 2 * Pp
    said = (f"{name}: {_n(O, 'occurrence')}"
            + (f" ({U} untranslatable, left out of its precision)" if U else "")
            + f" and {_n(G, 'ground truth triple')} ({k} within strict reach); "
            f"{_n(Pp, 'pair')} that count{'s' if Pp == 1 else ''} for it at the partial level ({Pe} exact, "
            f"{Pp - Pe} partial), {Sp} of them strict")
    if (against or Pp - Sp) and O + G <= TOO_FEW:
        what = (f"the {against} of them with no pair that counts for it at the partial level" if against
                else f"its {_n(Pp - Sp, 'pair')} that isn't strict")
        return _end(f"{said}: {_too_few(O, G, what)}" + many)
    causes = []
    if G - k:
        causes.append(f"{G - k} of its ground truth triples {_are(G - k)} out of strict reach (no checked row "
                      f"translates to their predicate, subject class, or object class), so {_they(G - k)} be in a "
                      f"strict pair: "
                      f"{_gap('predicate or entity class')}")
    if Pp - Sp:
        causes.append(f"in {_n(Pp - Sp, 'pair')}, the two triples differ in {_DIFFER[table]}: "
                      + (f"every one of this row's ground truth triples is within strict reach, so either step 060's extraction "
                         f"gave a wrong {_DIFFER[table]}, or a row of the translation table translates one to the "
                         f"wrong one" if k == G else
                         f"the ground truth triple is out of strict reach (above), step 060's extraction gave a wrong "
                         f"{_DIFFER[table]}, or a row of the translation table translates one to the wrong one; the "
                         f"counts don't tell which"))
    if G - Pp:
        them = "it" if G - Pp == 1 else "them"
        did = (f"step 060's extraction left the fact out, gave {them} {_OTHER[table]}, or wrote a subject instance "
               f"or object instance too differently to pair even at the partial level ({PAIRS_DEF})")
        causes.append(f"{_n(G - Pp, 'ground truth triple')} {_has(G - Pp)} no pair that counts for it (each against its "
                      f"recall): "
                      + (f"{'all ' if G - Pp > 1 else ''}within strict reach; among the causes, {did}, or "
                         f"{NOT_RULED_OUT}; the counts don't tell which (every cause: {RECALL_CAUSES})" if k == G else
                         f"either some are out of strict reach (above), or, among the other causes, {did}, or "
                         f"{NOT_RULED_OUT}; the counts don't tell which (every cause: {RECALL_CAUSES})"))
    if Ot - Pp:
        causes.append(f"{_n(Ot - Pp, 'occurrence')} {_has(Ot - Pp)} no pair that counts for it (each against its "
                      f"precision): step 060's "
                      f"extraction stated a fact the ground truth doesn't have (wrong, or right but not annotated), "
                      f"stated one the ground truth has with {_OTHER[table]} or in words too different to pair even at "
                      f"the partial level, restated a fact already in a pair, or repeated an occurrence (multiplicity "
                      f"> 1); or a row of the translation table translates its predicate or an entity class to the "
                      f"wrong component class of the ground truth schema, or with the wrong swap_subject_and_object; "
                      f"among others, the counts don't tell which (each occurrence, with its pair if any: "
                      f"`per_record.md`; every cause: {PRECISION_CAUSES})")
    if Pp - Pe:
        causes.append(_partial(Pp - Pe))
    return _end(_causes(said, causes, "Nothing counts against it at the partial level: every occurrence and ground "
                                      "truth triple is in a strict pair that counts for it") + many)


def _partial(k: int) -> str:
    return (f"{k} of these pairs {'is' if k == 1 else 'are'} partial, not exact: in each, the subject instance or "
            f"object instance of one triple is inside the other's as whole words, not the same ({PAIRS_DEF}), so at "
            f"the exact level its two triples count against this row (column *Counted against it (exact)*): step "
            f"060's extraction wrote the instance more or less fully than the ground truth, or the pair is a wrong one "
            f"(`070_evaluate/metrics/pairs.md`, *When a pair isn't the same fact*)")


def record_reading(r: dict) -> str:
    """One line reading a row of the table per record (stats.per_record), at the exact level."""
    O, G, W, Ws = r["occurrences"], r["ground_truth_triples"], r["within_reach"], r["within_strict_reach"]
    Pe, Se = r["exact"]["pairs"], r["exact"]["strict_pairs"]
    many = _multiplied(r["occurrences_multiplicity_above_1"])
    s = f"Record {r['id'][:8]} (pool position {r['position']}): "
    if not O + G:
        return _end(s + "no occurrences and no ground truth triples: nothing to compare." + many)
    s += (f"{_n(O, 'occurrence')} and {_n(G, 'ground truth triple')} ({W} within reach, {Ws} within strict "
          f"reach); {_n(Pe, 'exact pair')}, {Se} of them strict; exact recall {_no_value(r['exact']['recall'])}, exact "
          f"precision {_no_value(r['exact']['precision'])}"
          + (f" ({_n(r['pending_pairs'], 'occurrence')} matching a fact that waits on an expert, left out of its "
             f"precision)" if r.get("pending_pairs") else "")
          + (f" ({_n(r['untranslatable'], 'untranslatable occurrence')}, left out of its precision: section *Schema "
             f"fit* of the report)" if r.get("untranslatable") else ""))
    against = r["counted_against"]
    if (against or Pe - Se) and O + G <= TOO_FEW:
        what = (f"the {against} of them with no exact pair" if against
                else f"its {_n(Pe - Se, 'exact pair')} that isn't strict")
        return _end(f"{s}: {_too_few(O, G, what)}" + many)
    causes = []
    if G - W:
        causes.append(f"{G - W} of its ground truth triples {_are(G - W)} out of reach (no checked row translates a "
                      f"predicate of the current schema to theirs), so {_they(G - W)} be in any pair: "
                      f"{_gap('predicate')}")
    if Pe - Se:
        causes.append(f"in {_n(Pe - Se, 'exact pair')}, the two triples differ in subject class or object class: "
                      + ("every ground truth triple of the record is within strict reach, so either step 060's "
                         "extraction gave a wrong entity class, or a row of the translation table translates one to "
                         "the wrong one" if Ws == G else
                         "the ground truth triple is out of strict reach, step 060's extraction gave a wrong entity "
                         "class, or a row of the translation table translates one to the wrong one; the counts don't "
                         "tell which"))
    # every exact pair's ground truth triple is within reach; an untranslatable occurrence is judged neither way
    missing, unpaired = W - Pe, O - r.get("untranslatable", 0) - Pe
    if missing > unpaired:
        causes.append(f"{missing} of its ground truth triples within reach {_has(missing)} no exact pair, but only "
                      f"{unpaired} of its occurrences {'lacks' if unpaired == 1 else 'lack'} one, so at least "
                      f"{missing - unpaired} of the record's facts within reach have no occurrence left that could "
                      f"pair with them: among the causes, step 060's extraction left them out, or {NOT_RULED_OUT}; "
                      f"the counts don't tell which (every cause: {RECALL_CAUSES})")
    elif unpaired > missing:
        causes.append(f"{unpaired} of its occurrences {_has(unpaired)} no exact pair, but only {missing} of its ground "
                      f"truth triples within reach {'lacks' if missing == 1 else 'lack'} one, so at least {unpaired - missing} of its occurrences state no "
                      f"fact among those ground truth triples: step 060's extraction stated facts the ground truth "
                      f"doesn't have (wrong, or right but not annotated), stated with a predicate within reach a fact "
                      f"the ground truth has with one out of reach, restated a fact already in an exact pair, or repeated "
                      f"an occurrence (multiplicity > 1), among others; the counts don't tell which (every cause: "
                      f"{PRECISION_CAUSES})")
    elif missing:
        causes.append(f"{missing} of its ground truth triples within reach and {missing} of its occurrences have no "
                      f"exact pair: the counts don't tell whether step 060's extraction left facts out, stated them "
                      f"with another predicate or in other words (column *Pairs (partial)*: how many pair at the "
                      f"partial level), or stated facts the ground truth doesn't have")
    return _end(_causes(s, causes, "Nothing counts against it at the exact level: every occurrence and ground truth "
                                   "triple is in a strict exact pair") + many)


def row_readings(lines: list) -> list:
    """The numbered list below a table: one reading per row shown, in the table's order."""
    return ["Reading each row: one line per row above, in the same order. Each line gives the counts it rests on "
            "and, for each thing that counts against the row, the step that can cause it (step 040's schema, the "
            "translation table, step 060's extraction, or the ground truth), among those the counts leave possible "
            "(the counts never rule out every other: each full list is in `070_evaluate/metrics/recall.md` and "
            "`precision.md`). "
            f"Every cause a line can name, the rule (numbers and conditions) that names it, and the threshold for "
            f"too few: {RULES}.", ""] + [f"{i}. {line}" for i, line in enumerate(lines, 1)] + [""]
