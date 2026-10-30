"""
helpers/annotator/server.py -- the annotation tool's local server (started by
helpers/annotate.py).

It serves one page (page.html) and a small JSON API, on this computer only
(127.0.0.1): nothing leaves the laptop, no model is called, and only
Python's standard library is used.

What it reads
    outputs/intermediate_results/050_annotate/drafted_triples_batch<N>.csv   step 050's drafted batches
    annotations/ground_truth/batch_<NNN>.csv                                  the ground truth files
    outputs/intermediate_results/020_clean/records.jsonl                     each record's text
    outputs/intermediate_results/030_split/splits.json                       each record's pool position and part
    annotations/ground_truth_schema.txt                   the ground truth schema
    annotations/component_class_mapping.csv                                             the translation table
    outputs/intermediate_results/060_extract/schema_used.json                the current schema's definitions
    outputs/intermediate_results/060_extract/extracted_triples.csv           an example triple per predicate
    outputs/intermediate_results/070_evaluate/metrics.json                    evaluation's suggestions for (none) rows
    outputs/intermediate_results/070_evaluate/compared_triples.csv                    evaluation's partial pairs
    annotations/partial_pair_reviews.csv                                     your verdicts on them
    annotations/schema_additions.txt                                         the schema additions
    annotations/reviews/                                                     reviewers' comments (shown, never changed)
    annotations/left_out.md                                                  what the ground truth leaves out on purpose (shown, never changed)
    annotations/README.md                                                    each view's How to use this view
    annotations/guidelines.md, docs/terminology.md, any other .md of the repository   what the Help menus open
    helpers/annotator/fonts/*.woff2                                          the page's typefaces
    outputs/intermediate_results/060_extract/extracted_triples_details.json  extraction's component classes outside the schema

What it writes: ONLY annotations/ground_truth/batch_<NNN>.csv,
annotations/component_class_mapping.csv, annotations/partial_pair_reviews.csv,
annotations/schema_additions.txt, and additions to
annotations/ground_truth_schema.txt (nothing else in it
changes).
    - Opening drafted batch N for the first time copies it to
      annotations/ground_truth/batch_<NNN>.csv (N with three digits); from
      then on that copy is what's shown and edited. The drafted batch's file
      in outputs/ is never changed.
    - Every edit is saved to that file at once (the page sends the batch, the
      server writes it under a temporary name and renames it).
    - The drafted batch's flags column isn't kept: the checks are recomputed live.

The translation table (step 070's, common/common_helpers/component_class_mapping.py) is shown row by
row, each component class with its definition, and a person's choices are saved to it
at once: component_class_in_gtt (a component class of the ground truth schema, or (none)),
swap_subject_and_object (predicates only) and checked. Rows can't be added
or reordered here, and the only rows that can be removed are a component class's
repeated ones (common/common_helpers/component_class_mapping.repeats), and a save keeps any rows step 070 added since
the page was loaded; if the rows the page shows have changed in the file, the
save is refused, so nothing is overwritten.

Schema additions: the entries of annotations/schema_additions.txt, to add,
edit or delete through a form, so the file's layout can't go wrong; the
comments at its top are kept. Every entry needs a definition and a source;
a source naming the ground truth must say "tuning" and name tuning records
only (common/common_helpers/schema_io.ground_truth_source_problem, the same check step 060
applies). A file with lines the layout can't read is not rewritten (fix it
by hand first). Extraction's last list of component classes outside the schema is shown
alongside, each ready to add with its source.

Help: each view's Help menu (How to use this view) shows the section of
annotations/README.md about that view (HELP_SECTIONS), so the tool's
explanation lives in one place.

What to do next: the home page shows the project's status
(common/common_helpers/status.py, /api/status), the same list as
`py run_pipeline.py --status`: each view's box its own count, and every item
with the section of docs/upkeep.md that explains it.

Partial pairs (common/common_helpers/partial_reviews.py): evaluation's last run's partial
pairs of TUNING records, each with its two triples and the record's text, for a
person to mark "same fact" or "not the same fact"; pairs ruled out earlier
are shown too, so a verdict can be changed. Where the two triples' subject
instances, predicates, or object instances differ once evened out (norm_text,
as step 070 compares them), the page fills both fields and marks the words
only one side has (pair_differences). Held-out records are never
shown or accepted (reviewing them would mean looking at held-out results).

The checks are step 050's own, all from common/common_helpers/validate.py (source texts,
"is it in the text", and whether each entity class, predicate, and pattern
is in the ground truth schema), shown in plain words (MESSAGES). The ground
truth schema's patterns are its file's plus every one the ground truth uses
(common/common_helpers/ground_truth.with_coined), so a pattern is flagged only
the first time it is used, for a look (a wrong entity class or direction),
and never needs adding. One check is the tool's own (connection_problems): a
ground truth triple that no chain of the record's ground truth triples links to
the record's id is flagged (not_connected), so the fact that connects it is
looked for. Another is too (qualifier_problems): a subject instance given two or
more values by one of rule 9's predicates is flagged (several_qualifiers), since
rule 9 may have lost which fact each value went with. A third (slash_list_problems):
an instance holding one item of a "/" or "+" list whose items the record's text
never names separately is flagged (slash_list_split), since rule 12 keeps such a
list whole. The component classes
suggested as you type are the ground truth schema's, plus those coined in the
ground truth (common/common_helpers/ground_truth.with_coined), so a coined
component class is offered for reuse. A coined component class is an error
until it is added to the ground truth schema, since it could be a typo, and
step 070 stops while a finished record uses one.

Adding to the ground truth schema: each error "not in the ground truth schema" on a row
has a button that adds the entity class or predicate, with the one-line definition the
person types; so does the list, in the ground truth schema's overview (Help -> Ground
truth schema), of what the ground truth uses that the ground truth schema lacks
(ground_truth_schema_gaps). The file is changed by
common/common_helpers/schema_io.add_to_ground_truth_schema, which adds one entry,
checks that nothing else changed, and otherwise puts the file back. A component
class gets a "source:" line naming the ground truth records using it, by part
("ground truth tuning #3; held-out #8"), so it can be told whether held-out
records shaped its component classes.

The ground truth schema is frozen for held-out records (annotations/guidelines.md,
Before you start): in a held-out record, an entity class or predicate the ground truth
schema lacks gets its own message (_frozen_message) and no button to add it; adding one
that a held-out record uses is refused; and adding, renaming, merging, or changing a
definition is refused while the record shown is held-out (refuse_if_held_out; the page sends the id of the
record shown). Step 070 notes an entry whose "source:" line names a held-out record.
"""
from __future__ import annotations

import collections
import csv
import difflib
import io
import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

from common.audit import ORIGIN_FIELD
from common.chunking import full_text
from common.files import write_csv, write_text
from common.ground_truth import (COLUMNS, DRAFT_NUMBERED, DRAFT_PATTERN, FILE_COLUMNS, GROUND_TRUTH_DIR, NUMBERED, PATTERN,
                                 HELD_OUT, KIND_KEYS, TUNING, draft_name, file_name,
                                 ground_truth_schema_gaps as schema_gaps, pattern_of,
                                 read_ground_truth, read_pool, uses_of, with_coined)
from common.component_class_mapping import (CHECKED, COLUMNS as MAPPING_COLUMNS, IN_CRT, IN_GTT, MAPPING_PATH,
                                            MISSING_TARGET, NONE, NOW_EXISTS, REPEATED, SHARED, STALE, SUGGESTED,
                                            VALUES as MAPPING_VALUES, crt_definitions, gtt_definition,
                                            gtt_definitions, is_checked, is_missing_target, is_stale_gtt,
                                            read_mapping, repeats, row_states, sharing, stale_in, condition_text)
from common.partial_reviews import (COLUMNS as REVIEW_COLUMNS, EXACT_PAIR, EXTRACTED_ONLY, GROUND_TRUTH_ONLY, NOT_SAME,
                                    PARTIAL_PAIR, REVIEWS_PATH, SAME, row_key, verdict_of)
from common.records_io import HARVEST_DIR, catalog_page_link, harvest_date, harvest_file, load_records, saved_copy
from common.review_comments import (CHANGED, GONE, NOT_VERIFIED, TOPIC_HEADINGS, REVIEWS_DIR as REVIEWER_COMMENTS_DIR,
                                    UNCHANGED, read_all as read_reviewer_comments)
from common.expert_questions import OPEN, QUESTIONS_PATH, read_questions
from common.left_out import LEFT_OUT_PATH, NO_RULE, read_left_out, rule_ref
from common.schema_io import ONE_WORD, addition_problem, additions_entries, add_to_ground_truth_schema, additions_header, additions_text, \
    pattern_key, read_ground_truth_schema, read_schema, redefine_in_ground_truth_schema, rename_in_ground_truth_schema
from common.status import LOOK, TO_DO, project_status
from common.step import ANNOTATIONS_DIR, RESULTS_DIR, ROOT
from common.text_match import Text, norm_text
from common.triples_io import (ENTRY_CLASS, ENTRY_PREDICATE, ENTRY_SOURCE, UNDECIDED,
                               component_class_key, is_describes)
from common.validate import (DATASET_SUBJECT_NOT_TITLE, DESCRIBES_CLASS_NOT_IN_SCHEMA, DESCRIBES_SUBJECT_NOT_ID,
                             DESCRIBES_UNDECIDED, EMPTY, NOT_CONNECTED, NO_SOURCE_TEXT, OBJECT_CLASS_NOT_IN_SCHEMA,
                             OBJECT_NOT_IN_SOURCE, OBJECT_NOT_IN_TEXT, PATTERN_NOT_IN_SCHEMA, PATTERN_NOT_PINNED,
                             PREDICATE_NOT_IN_SCHEMA, QUALIFIER_PREDICATES, SEVERAL_QUALIFIERS, SLASH_LIST_SPLIT, SOURCE_NOT_IN_TEXT,
                             SUBJECT_CLASS_NOT_IN_SCHEMA, SUBJECT_EQUALS_OBJECT, SUBJECT_NOT_IN_SOURCE,
                             SUBJECT_NOT_IN_TEXT, SchemaEntries, check_against_schema, check_describes,
                             check_triple_instance)

DRAFTS_DIR = RESULTS_DIR / "050_annotate"
RECORDS = RESULTS_DIR / "020_clean" / "records.jsonl"
SCHEMA_USED = RESULTS_DIR / "060_extract" / "schema_used.json"
EXTRACTED = RESULTS_DIR / "060_extract" / "extracted_triples.csv"
METRICS = RESULTS_DIR / "070_evaluate" / "metrics.json"
COMPARED = RESULTS_DIR / "070_evaluate" / "compared_triples.csv"
#: An occurrence's triple in compared_triples.csv (columns extracted_* and translated_*).
OCCURRENCE = ("subject", "subject_class", "predicate", "object", "object_class")
ADDITIONS = ANNOTATIONS_DIR / "schema_additions.txt"
README = ANNOTATIONS_DIR / "README.md"
GUIDELINES = ANNOTATIONS_DIR / "guidelines.md"           # what to write in the ground truth: Help -> Guidelines
TERMINOLOGY = ROOT / "docs" / "terminology.md"            # each term's definition, shown when a linked term is hovered
#: The heading of annotations/README.md that explains each view of the page.
HELP_SECTIONS = {"batch": "## Annotating ground truth: the annotation tool",
                 "mapping": "### Checking the translation table",
                 "partial": "### Reviewing partial pairs",
                 "additions": "### Adding to the schema additions",
                 "vocab": "### The ground truth schema",
                 "reviews": "### Reading reviewers' comments",
                 "leftout": "### Reading what the ground truth leaves out"}
#: Sections shown after a view's own: the whole tool's two lists, with Ground truth's (the view used most).
HELP_ALSO = {"batch": ("### What the tool can do", "### What the tool can't do")}
EXTRACTION_DETAILS = RESULTS_DIR / "060_extract" / "extracted_triples_details.json"
SPLITS = RESULTS_DIR / "030_split" / "splits.json"
HARVEST = HARVEST_DIR                               # step 010's saved harvest, for a record's saved copy
GROUND_TRUTH_SCHEMA = ANNOTATIONS_DIR / "ground_truth_schema.txt"
PAGE = Path(__file__).with_name("page.html")
#: The page's typefaces (Libre Franklin and JetBrains Mono, SIL Open Font License: the OFL-*.txt beside them).
FONTS = Path(__file__).with_name("fonts")

#: Each check's message for the page (the codes: common/common_helpers/validate.py; what each means:
#: 050_annotate/050_annotate.md, *Checks on each row*); each {placeholder} is filled with the component class concerned.
MESSAGES = {
    NO_SOURCE_TEXT: "No source text: without one, this ground truth triple can't be checked against the record's text. Select the "
                      "passage in the record's text that states this fact, then press \"Use selection\".",
    SOURCE_NOT_IN_TEXT: "The source text isn't in the record's text: it may have been retyped or cut, so this "
                          "ground truth triple can't be checked. Select the passage in the record's text, then press \"Use selection\" to "
                          "copy it exactly.",
    SUBJECT_NOT_IN_TEXT: "The subject instance isn't in the record's text: a typo, or reworded. Fix a typo; if it's "
                           "reworded on purpose, nothing to do.",
    OBJECT_NOT_IN_TEXT: "The object instance isn't in the record's text: a typo, or reworded. Fix a typo; if it's "
                          "reworded on purpose, nothing to do.",
    SUBJECT_NOT_IN_SOURCE: "The subject instance isn't in this ground truth triple's source text: the source text may be the wrong "
                             "passage, or too short. A source text contains words for the subject, the predicate and the object; "
                             "when the subject is named only in an earlier sentence, it runs from where it is named to the end of the "
                             "fact (rule 7 of \"Writing a classed triple\"). Select such a passage, then press \"Use selection\"; "
                             "if the passage has words for the subject that differ from the instance (a list split, a qualifier "
                             "taken out, one wording within a record), nothing to do.",
    OBJECT_NOT_IN_SOURCE: "The object instance isn't in this ground truth triple's source text: the source text may be the wrong "
                            "passage, or too short. A source text contains words for the subject, the predicate and the object "
                            "(rule 7 of \"Writing a classed triple\"). Select such a passage, then press \"Use selection\"; "
                            "if the passage has words for the object that differ from the instance (a list split, a qualifier "
                            "taken out, one wording within a record), nothing to do.",
    SUBJECT_EQUALS_OBJECT: "The subject instance and the object instance are the same: a fact relates two different "
                             "things, so one of them is probably wrong. Correct it.",
    DATASET_SUBJECT_NOT_TITLE: "This triple's subject is a Dataset, but not this record's title ({title}). If it is this "
                                 "record's dataset, use the title (rule 13); if it is another dataset, such as an "
                                 "input, keep it.",
    SUBJECT_CLASS_NOT_IN_SCHEMA: "\"{subject_class}\" isn't an entity class of the ground truth schema: a new one, "
                                   "or a typo. Keep it only if none of the schema's fits. "
                                   "If it's new, add it to the ground truth schema with the button below, "
                                   "giving a one-line definition: until then, step 070 can't evaluate a finished record that uses it.",
    OBJECT_CLASS_NOT_IN_SCHEMA: "\"{object_class}\" isn't an entity class of the ground truth schema: a new one, "
                                  "or a typo. Keep it only if none of the schema's fits. "
                                  "If it's new, add it to the ground truth schema with the button below, "
                                  "giving a one-line definition: until then, step 070 can't evaluate a finished record that uses it.",
    PREDICATE_NOT_IN_SCHEMA: "\"{predicate}\" isn't a predicate of the ground truth schema: a new one, or a typo. "
                               "Keep it only if none of the schema's fits. "
                               "If it's new, add it to the ground truth schema with the button below, "
                               "giving a one-line definition: until then, step 070 can't evaluate a finished record that uses it.",
    PATTERN_NOT_IN_SCHEMA: "No other ground truth triple uses {predicate} between {subject_class} and "
                             "{object_class}: a pattern used for the first time, or a wrong entity class or "
                             "direction. If it's right, there's nothing to do: from now on it's one of the ground "
                             "truth schema's patterns.",
    PATTERN_NOT_PINNED: "{predicate} is pinned in the ground truth schema (its \"only:\" line): it joins only "
                          "the entity classes listed there, not {subject_class} and {object_class}. Use another "
                          "predicate, or fix the entity classes.",
    EMPTY: "Subject, predicate, or object is empty: a ground truth triple states a fact only with all three. "
             "Fill in the empty ones, or delete it.",
    DESCRIBES_UNDECIDED: "No describes class yet (the describes triple's object class is X or empty). Type or "
                           "pick the describes triple's object class: the entity class of its object instance.",
    DESCRIBES_CLASS_NOT_IN_SCHEMA: "\"{object_class}\" isn't an entity class of the ground truth schema: a new "
                                     "one, or a typo. Keep it only if none of the schema's fits. "
                                     "If it's new, add it to the ground truth schema with the button below, "
                                     "giving a one-line definition: until then, step 070 can't evaluate a finished record that uses it.",
    DESCRIBES_SUBJECT_NOT_ID: "The describes triple's subject should be the record's id.",
    # the tool's own check (connection_problems), on a record's rows together: {piece} is filled with the component
    # instances this ground truth triple is connected to
    NOT_CONNECTED: "No chain of ground truth triples links this ground truth triple to the record's id (through "
                     "the describes triple). Look for the fact that connects it, and add it only if the "
                     "record states it (annotations/guidelines.md, Finishing a record). Not connected: {piece}.",
    # the tool's own check (slash_list_problems), on a record's rows and its text
    SLASH_LIST_SPLIT: "The {slot} instance \"{instance}\" looks like one item of the list \"{group}\", joined by \"/\" or "
                        "\"+\", but the record's text never names that list's items separately: {missing}. Rule 12 of "
                        "\"Writing a classed triple\" splits such a list only when the text also names its items "
                        "separately somewhere else; otherwise it stays whole, as written (\"RSI 1/2/3\"). Write "
                        "the list whole, as written; if the item is named separately in words this check doesn't "
                        "match, nothing to do.",
    # the tool's own check (qualifier_problems), on a record's rows together
    SEVERAL_QUALIFIERS: "\"{subject}\" has {count} ground truth triples with {predicate}: {values}. Rule 9 of "
                          "\"Writing a classed triple\" takes such a qualifier out of the instance it was in, so if "
                          "each of these came from a different fact of the record (e.g. \"Level 2/3 (EDR/RDR) data\": "
                          "Level 2 goes with the EDR data, Level 3 with the RDR data), the ground truth no longer says "
                          "which goes with which. That loss is known and accepted (docs/improvements.md, Rule 9 can lose "
                          "which fact a qualifier went with): nothing to fix, since rule 9 always applies. Read the "
                          "record's text to see whether it happened here; if the values describe \"{subject}\" "
                          "together (a dataset observed at daytime and at nighttime), nothing was lost.",
}


#: Added to subject_not_in_source / object_not_in_source when the instance is elsewhere in the record's text (the
#: row has no subject_not_in_text / object_not_in_text); {slot} is "subject" or "object".
ELSEWHERE_IN_TEXT = (" However, the {slot} instance does appear elsewhere in the record's text, so it may be written "
                     "this way on purpose, to follow a rule: e.g. rule 13 of \"Writing a classed triple\" (one wording "
                     "for a thing within a record) or rule 2 of \"What counts as a fact\" (the title states facts "
                     "too); if so, nothing to do.")


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

class Data:
    """Everything the page needs besides the batch itself, loaded once."""

    def __init__(self):
        self.records = load_records(RECORDS) if RECORDS.exists() else {}
        self.positions, self.parts = {}, {}
        if SPLITS.exists():
            pool = read_pool(SPLITS)
            self.positions = {r["id"]: r["position"] for r in pool}
            self.parts = {r["id"]: r.get("part") for r in pool}            # "tuning" or "held-out"
        self.read_hand()
        self._texts = {}

    def read_hand(self) -> None:
        """(Re)read the ground truth schema: at the start, and after the page adds to it."""
        hand = read_ground_truth_schema(GROUND_TRUTH_SCHEMA) if GROUND_TRUTH_SCHEMA.exists() else \
            {"entity_classes": {}, "predicates": {}, "patterns": []}
        self.hand, self.schema_entries = hand, SchemaEntries(hand)

    def text(self, rid: str) -> Text | None:
        if rid not in self.records:
            return None
        if rid not in self._texts:
            self._texts[rid] = Text(full_text(self.records[rid]))
        return self._texts[rid]


def _read_rows(path: Path) -> list:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return [{c: (row.get(c) or "").strip() for c in FILE_COLUMNS} for row in csv.DictReader(fh)
                if (row.get("id") or "").strip()]


def _group(rows: list) -> list:
    """[(id, [rows])], in the file's order."""
    order, grouped = [], {}
    for row in rows:
        if row["id"] not in grouped:
            order.append(row["id"])
            grouped[row["id"]] = []
        grouped[row["id"]].append(row)
    return [(rid, grouped[rid]) for rid in order]


def check_row(data: Data, row: dict, title: str, uses: collections.Counter | None = None) -> list:
    """The row's problems, as {"code", "message", "type": "error" | "flag"}. uses: how many ground truth triples use
    each pattern (pattern_uses), this row among them: a pattern the file lacks is flagged only where no other
    ground truth triple uses it."""
    if is_describes(row):
        errors, flags = check_describes(row, row["id"], data.schema_entries)
    elif not (row["subject"] and row["predicate"] and row["object"]):
        errors, flags = [EMPTY], []
    else:
        text = data.text(row["id"])
        errors, flags = check_triple_instance(row, text, title) if text is not None else ([], [])
        flags = flags + check_against_schema(row, data.schema_entries)
        if uses is not None and uses[pattern_of(row)] > 1:
            flags = [c for c in flags if c != PATTERN_NOT_IN_SCHEMA]
    # an entity class or predicate the ground truth schema lacks must be added to it (or the typo fixed): step 070
    # stops on one in a finished record, so it's an error to fix, not a flag; a pattern used for the first time
    # stays a flag
    every = errors + flags
    errors = errors + [c for c in flags if c in ADDS]
    flags = [c for c in flags if c not in ADDS]
    held_out = data.parts.get(row.get("id")) == HELD_OUT
    return [{"code": c, "type": kind, "add": None if held_out and c in ADDS else _offer(c, row, every),
             "message": _frozen_message(data, c, row) if held_out and c in ADDS else _message(c, row, every, title)}
            for kind, codes in (("error", errors), ("flag", flags)) for c in codes]


#: What to do instead of changing the ground truth schema while annotating a held-out record (annotations/guidelines.md).
INSTEAD = ("use the ground truth schema's {kind} that fits; if none fits, delete the ground truth triple and write the "
           "fact in annotations/left_out.md, with a question for the experts (annotations/guidelines.md, Before you start)")


def _frozen_message(data: Data, code: str, row: dict) -> str:
    """The message of an entity class or predicate the ground truth schema lacks, in a held-out record: the ground
    truth schema is frozen for held-out records, so it can't be added from one."""
    kind, column = ADDS[code]
    article = "an" if kind == "entity class" else "a"
    return (f"\"{row.get(column) or '(none)'}\" isn't {article} {kind} of the ground truth schema, and this is a held-out "
            f"record (pool position {data.positions.get(row['id'], '?')}): the ground truth schema is frozen while "
            f"annotating held-out records, so nothing can be added to it from this record. If it's a typo, fix it; "
            f"otherwise " + INSTEAD.format(kind=kind) + ".")


def refuse_if_held_out(data: Data, item: dict, what: str) -> None:
    """Refuse a change to the ground truth schema (adding, renaming, merging, changing a definition) while the record
    shown is held-out."""
    rid = str(item.get("record") or "")
    if data.parts.get(rid) == HELD_OUT:
        raise ValueError(f"the record shown, {rid} (pool position {data.positions.get(rid, '?')}), is a held-out "
                         f"record, and the ground truth schema is frozen while annotating held-out records, so {what} "
                         f"is refused. For this record, " + INSTEAD.format(kind="entity class or predicate")
                         + ". If a tuning record needs the change, make it with a tuning record shown.")


def _message(code: str, row: dict, every: list, title: str = "") -> str:
    """The check's message, filled in; a "not in the source text" flag says so when the instance is still in the
    record's text (its "not in the text" flag absent)."""
    message = MESSAGES[code].format(title=title, **{k: row.get(k) or "(none)" for k in COLUMNS})
    if code in NOT_IN_SOURCE and NOT_IN_SOURCE[code][0] not in every:
        message += ELSEWHERE_IN_TEXT.format(slot=NOT_IN_SOURCE[code][1])
    return message


#: Each "not in the source text" flag: its "not in the text" flag, and its slot.
NOT_IN_SOURCE = {SUBJECT_NOT_IN_SOURCE: (SUBJECT_NOT_IN_TEXT, "subject"),
                 OBJECT_NOT_IN_SOURCE: (OBJECT_NOT_IN_TEXT, "object")}


def connection_problems(rid: str, rows: list) -> list:
    """For each of a record's rows, its not_connected flag (a list of one), or []. The rows form a graph: each
    ground truth triple joins its subject instance and its object instance (direction ignored; instances compared
    as norm_text evens them out), the describes triple joining the record's id to its title. A
    ground truth triple is connected when a chain of them links it to the record's id. Rows not filled in, or
    lacking a subject or an object, are skipped."""
    parent = {}

    def root(k: str) -> str:
        while parent.setdefault(k, k) != k:
            parent[k] = k = parent[parent[k]]
        return k

    ends = []
    for row in rows:
        subject = rid if is_describes(row) else str(row.get("subject") or "").strip()   # as save_batch writes it
        pair = (subject, str(row.get("object") or "").strip())
        ends.append(pair if all(pair) else None)
        if all(pair):
            parent[root(norm_text(pair[0]))] = root(norm_text(pair[1]))
    pieces = collections.defaultdict(dict)                 # {piece: {evened-out instance: its first spelling}}
    for pair in filter(None, ends):
        for x in pair:
            pieces[root(norm_text(x))].setdefault(norm_text(x), x)
    entry = root(norm_text(rid))
    return [[] if pair is None or root(norm_text(pair[0])) == entry else
            [{"code": NOT_CONNECTED, "type": "flag", "add": None, "message": MESSAGES[NOT_CONNECTED].format(
                piece=", ".join(f'"{x}"' for x in pieces[root(norm_text(pair[0]))].values()))}]
            for pair in ends]


#: The flags a person resolves by adding a component class to the ground truth schema: (kind, the row's column holding it).
ADDS = {SUBJECT_CLASS_NOT_IN_SCHEMA: ("entity class", "subject_class"),
        OBJECT_CLASS_NOT_IN_SCHEMA: ("entity class", "object_class"),
        DESCRIBES_CLASS_NOT_IN_SCHEMA: ("entity class", "object_class"),
        PREDICATE_NOT_IN_SCHEMA: ("predicate", "predicate")}


def qualifier_problems(rows: list) -> list:
    """For each of a record's rows, its several_qualifiers flag (a list of one), or []: a row whose predicate is one
    of rule 9's (QUALIFIER_PREDICATES), when another row gives the same subject instance (evened out, as norm_text
    does) the same predicate. Two values aren't always a loss (a dataset observed at daytime and at nighttime), so a
    flag, for a person to read the record. Rows lacking a subject instance, predicate, or object instance are skipped."""
    def key(row: dict):
        predicate = str(row.get("predicate") or "").strip()
        subject, obj = (str(row.get(c) or "").strip() for c in ("subject", "object"))
        return (norm_text(subject), predicate) if predicate in QUALIFIER_PREDICATES and subject and obj else None
    groups = collections.defaultdict(list)
    for row in rows:
        if (k := key(row)) is not None:
            groups[k].append(row)
    out = []
    for row in rows:
        same = groups.get(key(row), []) if key(row) is not None else []
        out.append([] if len(same) < 2 else [{"code": SEVERAL_QUALIFIERS, "type": "flag", "add": None,
                    "message": MESSAGES[SEVERAL_QUALIFIERS].format(
                        subject=str(row["subject"]).strip(), count=len(same), predicate=str(row["predicate"]).strip(),
                        values=", ".join(f'"{str(r["object"]).strip()}"' for r in same))}])
    return out


#: A list joined by "/" or "+" in a record's text: two or more items, no spaces inside an item ("2/3", "EDR/RDR",
#: "Terra+Aqua"), with the parentheses or brackets around it left out.
SLASH_LIST = re.compile(r"(?<![\w/+])[\w.\-]+(?:[/+][\w.\-]+)+(?![\w/+])")
#: Words that make a "/" part of an address, not a list.
NOT_A_LIST = ("://", "www.", "doi", ".gov", ".org", ".edu", ".com", ".html")


def slash_lists(text: str) -> list:
    """The record's "/" or "+" lists, as groups: a list and the lists right after it with as many items (in
    parentheses or not) are one group, since they name the same items twice ("Level 2/3 (EDR/RDR)": items "2" and
    "EDR", "3" and "RDR"). Each group: (its words in the text, its items per position, whether the text names every
    position's item separately, outside the group, the word right before it: "RSI" for "RSI 1/2/3")."""
    def word(m):                                        # the whitespace-separated word the match is in
        return text[text.rfind(" ", 0, m.start()) + 1:(text.find(" ", m.end()) + 1 or len(text) + 1) - 1].lower()
    found = [m for m in SLASH_LIST.finditer(text) if not any(w in word(m) for w in NOT_A_LIST)]
    groups, i = [], 0
    while i < len(found):
        group = [found[i]]
        while i + 1 < len(found) and len(re.split(r"[/+]", found[i + 1].group(0))) == len(re.split(r"[/+]", group[0].group(0)))                 and re.fullmatch(r"[\s()\[\]]*", text[group[-1].end():found[i + 1].start()]):
            i += 1
            group.append(found[i])
        i += 1
        start, end = group[0].start(), group[-1].end()
        rest = text[:start] + " " + text[end:]
        rest = SLASH_LIST.sub(" ", rest)                    # an item inside another list isn't named separately
        positions = list(zip(*[re.split(r"[/+]", m.group(0)) for m in group]))
        named = all(any(re.search(rf"(?<![\w]){re.escape(item)}(?![\w])", rest, re.I) for item in items)
                    for items in positions)
        before = re.findall(r"[\w.\-]+", text[max(0, start - 40):start])
        groups.append((text[start:end], positions, named, before[-1] if before else ""))
    # the same list written twice ("DFMI 2/3" in the title, "Level 2/3 (EDR/RDR)" in the notes) is named separately
    # when either place's group is
    named_words = {words for g in groups if g[2] for words in re.split(r"[\s()\[\]]+", g[0]) if words}
    return [(w, p, n or w in named_words, b) for w, p, n, b in groups]


def slash_list_problems(text: str, rows: list) -> list:
    """For each of a record's rows, its slash_list_split flags, or []: a subject or object instance that isn't in the
    record's text as written (evened out, as norm_text does) but holds, as a word, one item of a "/" or "+" list
    whose items the text never names separately (rule 12 of "Writing a classed triple": such a list stays whole). An
    instance in the text as written, or holding the whole list, isn't flagged. A flag, since the item may be named
    separately in words this check doesn't match."""
    whole = " ".join((text or "").lower().split())
    groups = [g for g in slash_lists(text or "") if not g[2]]

    def in_text(instance: str) -> bool:                 # as written, and not just the start of a list ("RSI 1/2/3")
        words = " ".join(instance.lower().split())
        return re.search(rf"(?<![\w]){re.escape(words)}(?![\w/+])", whole) is not None
    out = []
    for row in rows:
        found = []
        for slot in ("subject", "object"):
            instance = str(row.get(slot) or "").strip()
            if not instance or in_text(instance):
                continue
            for words, positions, _, before in groups:
                if norm_text(words) in norm_text(instance):
                    continue
                # a number alone ("3") is an item only beside the word before the list ("RSI 3", not "Level 3")
                if any(re.search(rf"(?<![\w]){re.escape(item)}(?![\w])", instance, re.I)
                       and (not item.isdigit() or re.search(rf"(?<![\w]){re.escape(before)}(?![\w])", instance, re.I))
                       for items in positions for item in items if before or not item.isdigit()):
                    found.append({"code": SLASH_LIST_SPLIT, "type": "flag", "add": None,
                                  "message": MESSAGES[SLASH_LIST_SPLIT].format(
                                      slot=slot, instance=instance, group=words,
                                      missing=", ".join(f'"{"/".join(items)}"' for items in positions))})
                    break
        out.append(found)
    return out


def _offer(code: str, row: dict, flags: list) -> dict | None:
    """What the page offers to add to the ground truth schema for one error, or None."""
    if code in ADDS:
        kind, column = ADDS[code]
        name = str(row.get(column) or "").strip()
        return {"entry_type": kind, "component_class": name} if component_class_key(name) else None
    return None


def pattern_uses(rows) -> collections.Counter:
    """How many ground truth triples use each pattern (common/common_helpers/ground_truth.pattern_of)."""
    return collections.Counter(k for r in rows if (k := pattern_of(r)))


def _is_blank(row: dict) -> bool:
    """A row with no subject, predicate, and object: in a file, the one row of
    a record that states no facts; on the page, a row not filled in yet."""
    return not (row["subject"] or row["predicate"] or row["object"])


def record_view(data: Data, rid: str, rows: list, finished: bool, uses: collections.Counter | None = None) -> dict:
    record = data.records.get(rid) or {}
    title = record.get("title") or ""
    return {
        "id": rid,
        "catalog_page_url": catalog_page_link(rid),
        "saved_copy": {"url": f"/api/raw_record?id={quote(rid, safe='')}", "harvest_date": harvest_date(HARVEST)}
                      if record and harvest_file(record, HARVEST) else None,     # None: not on this computer
        "maintainer": record.get("maintainer"),
        "position": data.positions.get(rid),
        "part": data.parts.get(rid),
        "title": title,
        "text": full_text(record) if record else None,
        "finished": finished,
        "rows": [{**r, "problems": check_row(data, r, title, uses) + extra + several + slash}
                 for r, extra, several, slash in zip(rows, connection_problems(rid, rows), qualifier_problems(rows),
                                                     slash_list_problems(full_text(record) if record else "", rows))],
    }


def batch_view(data: Data, n: int, path: Path) -> dict:
    """The batch as the page shows it: one entry per record, in the file's order."""
    gt = read_ground_truth()
    uses = pattern_uses(gt.rows)                       # this file's rows are among them, as saved
    records = [record_view(data, rid, [r for r in rows if not _is_blank(r)],
                           all(r["all_facts_extracted"] == "1" for r in rows), uses)
               for rid, rows in _group(_read_rows(path))]
    vocab = with_coined(data.hand, gt)
    return {"n": n, "file": path.name, "records": records,
            "entity_classes": sorted(vocab["entity_classes"]), "predicates": sorted(vocab["predicates"]),
            **definitions_view(data, gt), "patterns": patterns_view(data, gt),
            # the problems of a row the page adds, not filled in yet (so the page doesn't retype the message)
            "new_row_problems": [{"code": EMPTY, "type": "error", "add": None, "message": MESSAGES[EMPTY]}]}


def definitions_view(data: Data, gt=None) -> dict:
    """For the page's list of component classes and the definition under each component class field: each one's
    definition (empty for a coined one), and which are coined. Sent again after each save, as the schema may grow."""
    vocab = with_coined(data.hand, gt or read_ground_truth())
    return {"definitions": {"entity_classes": vocab["entity_classes"], "predicates": vocab["predicates"]},
            "coined": vocab["coined"]}


def patterns_view(data: Data, gt=None) -> list:
    """The ground truth schema's patterns (the file's, then every one the ground truth uses), for the page's
    pattern buttons under a ground truth triple: [subject class, predicate, object class]."""
    return [list(t) for t in with_coined(data.hand, gt or read_ground_truth())["patterns"]]


# --------------------------------------------------------------------------
# adding to the ground truth schema
# --------------------------------------------------------------------------

def _learned_from(data: Data, rows: list) -> str:
    """Where a component class was learned, as a "source:" line the source check
    (common/common_helpers/schema_io.ground_truth_source_problem) can read: the
    ground truth records using it, by part, as pool positions."""
    by_part, outside = {TUNING: set(), HELD_OUT: set()}, []
    for rid in dict.fromkeys(r["id"] for r in rows):
        if data.parts.get(rid) in by_part and rid in data.positions:
            by_part[data.parts[rid]].add(data.positions[rid])
        else:
            outside.append(rid)
    bits = [f"{part} " + ", ".join(f"#{p}" for p in sorted(ps)) for part, ps in by_part.items() if ps]
    bits += ["not in the pool: " + ", ".join(outside)] if outside else []
    return "ground truth " + "; ".join(bits) if bits else ""


def ground_truth_schema_gaps(data: Data, gt) -> dict:
    """What the ground truth uses that the ground truth schema lacks (common/common_helpers/ground_truth.py)."""
    return {"file": f"annotations/{GROUND_TRUTH_SCHEMA.name}", **schema_gaps(data.hand, gt)}


HAND_LOCK = threading.Lock()


def add_to_hand(data: Data, item: dict) -> str:
    """Add one component class (with its definition) to the ground truth
    schema; say what was added. It is written as the page sent it, with
    a "source:" line naming the ground truth records using it (in any
    spelling, compared as component_class_key does). One add at a time (HAND_LOCK):
    the server answers requests in parallel, and two adds at once could
    undo each other."""
    with HAND_LOCK:
        kind = item.get("entry_type")
        if kind not in KIND_KEYS:
            raise ValueError("entry_type must be entity class or predicate")
        name = str(item.get("component_class") or "").strip()
        refuse_if_held_out(data, item, f"adding {name}")
        uses = uses_of(read_ground_truth(), kind, name)
        held = sorted({(data.positions.get(r["id"], -1), r["id"]) for r in uses if data.parts.get(r["id"]) == HELD_OUT})
        if held:
            raise ValueError(f"{name} is used by {len(held)} held-out record(s): "
                             + ", ".join(f"pool position {p} ({rid})" for p, rid in held)
                             + ". The ground truth schema is frozen for held-out records, so it can't be added from them. "
                             f"In those records, " + INSTEAD.format(kind=kind)
                             + f". If a tuning record needs {name}, add it once no held-out record uses it.")
        source = _learned_from(data, uses)
        add_to_ground_truth_schema(GROUND_TRUTH_SCHEMA, kind, name, item.get("definition") or "", source=source)
        data.read_hand()
        return f"Added the {kind} {name} to {GROUND_TRUTH_SCHEMA.name}" + (f" (source: {source})" if source else "")


def list_batches() -> list:
    """Every drafted batch and ground truth file, newest first."""
    out, gt_files = [], {int(m.group(1)): p for p in sorted(GROUND_TRUTH_DIR.glob(PATTERN))
                         if (m := NUMBERED.fullmatch(p.name))}
    drafts = {int(m.group(1)): p for p in DRAFTS_DIR.glob(DRAFT_PATTERN)
              if (m := DRAFT_NUMBERED.fullmatch(p.name))} if DRAFTS_DIR.exists() else {}
    for n in sorted(set(gt_files) | set(drafts), reverse=True):
        gt = gt_files.get(n)
        rows = _read_rows(gt) if gt else []
        grouped = _group(rows)
        out.append({"n": n, "draft": drafts[n].name if n in drafts else None,
                    "ground_truth": gt.name if gt else None,
                    "records": len(grouped),
                    "finished": sum(all(r["all_facts_extracted"] == "1" for r in rs) for _, rs in grouped)})
    return out


def open_batch(n: int) -> Path:
    """The ground truth file of batch n, copied from its drafted batch's file the first time."""
    gt = GROUND_TRUTH_DIR / file_name(n)
    if not gt.exists():
        draft = DRAFTS_DIR / draft_name(n)
        if not draft.exists():
            raise FileNotFoundError(f"drafted batch {n} has no file (outputs/intermediate_results/050_annotate/{draft.name}) "
                                f"and no ground truth file (annotations/ground_truth/{gt.name}), so there is nothing "
                                f"to open. Pick another batch, or draft one with py 050_annotate/run.py.")
        write_csv(gt, FILE_COLUMNS, _read_rows(draft))
    return gt


def save_batch(data: Data, n: int, records: list) -> list:
    """Write the page's records to batch n's ground truth file, in the page's
    order, and return each row's problems (as the page sent them, so they
    line up with its rows). "finished" sets all_facts_extracted on every row
    of the record. Rows not filled in aren't written; a record left with no
    rows is written as one row holding only its id ("states no facts")."""
    out, problems = [], []
    # the patterns as they will be once this file is written: the other files' uses, and this one's from the page
    others = [r for r in read_ground_truth().rows if not r[ORIGIN_FIELD][0].split("#")[0].endswith("/" + file_name(n))]
    sent = [{c: str(r.get(c) or "").strip() for c in FILE_COLUMNS} for rec in records for r in rec.get("rows", [])]
    uses = pattern_uses(others + sent)
    for rec in records:
        mark = "1" if rec.get("finished") else "0"
        title = (data.records.get(rec["id"]) or {}).get("title") or ""
        written, found = [], []
        for r in rec.get("rows", []):
            row = {c: str(r.get(c) or "").strip() for c in FILE_COLUMNS}      # drafted_by: kept; empty on a row you add
            row["id"], row["all_facts_extracted"] = rec["id"], mark
            if is_describes(row):
                row["subject"], row["source_text"] = rec["id"], ENTRY_SOURCE
            found.append(check_row(data, row, title, uses))
            if not _is_blank(row):
                written.append(row)
        record = data.records.get(rec["id"])
        found = [f + extra + several + slash for f, extra, several, slash in zip(
            found, connection_problems(rec["id"], rec.get("rows", [])), qualifier_problems(rec.get("rows", [])),
            slash_list_problems(full_text(record) if record else "", rec.get("rows", [])))]
        out.extend(written or [{c: "" for c in FILE_COLUMNS} | {"id": rec["id"], "all_facts_extracted": mark}])
        problems.append(found)
    # written only when its content changes: a save with nothing new in it leaves the file (and Git) alone
    path = GROUND_TRUTH_DIR / file_name(n)
    now = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n") if path.exists() else None
    if now != _csv_bytes(FILE_COLUMNS, out).decode("utf-8"):
        write_csv(path, FILE_COLUMNS, out)
    return problems


# --------------------------------------------------------------------------
# the translation table
# --------------------------------------------------------------------------

def _gtt(data: Data) -> dict:
    """The ground truth schema by kind: {kind: {component class: definition}}: the file's own, as step 070 reads
    it, so a coined component class (used in the ground truth, not in the file yet) is never a translation's target."""
    return {kind: dict(data.hand[key]) for kind, key in KIND_KEYS.items()}


def _coined(data: Data) -> dict:
    """{kind: {component_class_key(coined component class)}}: the ones the ground truth uses that the file lacks."""
    coined = with_coined(data.hand, read_ground_truth())["coined"]
    return {kind: {component_class_key(n) for n in coined[key]} for kind, key in KIND_KEYS.items()}


def _gtt_definitions(gtt: dict) -> dict:
    """_gtt's result as common/common_helpers/component_class_mapping.gtt_definitions gives it:
    {kind: {component_class_key(component class): definition}}."""
    return gtt_definitions({key: gtt[kind] for kind, key in KIND_KEYS.items()})


def _crt() -> dict | None:
    """The current schema's definitions (common/common_helpers/component_class_mapping.crt_definitions),
    or None if step 060's schema_used.json isn't there."""
    if not SCHEMA_USED.exists():
        return None
    return crt_definitions(json.loads(SCHEMA_USED.read_text(encoding="utf-8")))


def mapping_view(data: Data) -> dict:
    """The table as the page shows it: every row, with the current schema's
    definition, whether the row is stale (checked against another definition
    in the current schema: "stale", only for a row of the current schema; in the
    ground truth schema: "stale_gtt"), whether its target is missing
    ("missing_target": not (none), and not in the ground truth schema file), an
    example triple for a predicate (the first one extraction kept with it), and
    the ground truth schema to choose from (the file's own component classes)."""
    if not MAPPING_PATH.exists():
        return {"found": False, "rows": [], "gtt": {}}
    crt = _crt()
    examples = {}
    if EXTRACTED.exists():
        with open(EXTRACTED, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if not is_describes(r):
                    examples.setdefault(component_class_key(r.get("predicate")),
                                        {"subject": r.get("subject") or "", "object": r.get("object") or ""})
    gtt = _gtt(data)
    gtt_now = _gtt_definitions(gtt)
    table = read_mapping(MAPPING_PATH)
    repeated = repeats(table)
    extra = {line for r in repeated for line in r["lines"]}
    same_name = {kind: {component_class_key(n): n for n in names} for kind, names in gtt.items()}
    suggested = {}                                    # evaluation's last suggestions for (none) rows
    if METRICS.exists():
        for s in json.loads(METRICS.read_text(encoding="utf-8")).get("translation_suggestions", []):
            suggested[(s["kind"], component_class_key(s["component_class_from_past_or_crt_schema"]))] = s["component_class_in_gtt"]
    shared = sharing(table, crt)
    rows = []
    for r in table:
        key = component_class_key(r["component_class_from_past_or_crt_schema"])
        same, hint = same_name.get(r["kind"], {}).get(key), suggested.get((r["kind"], key))
        rows.append({**r, "same_component_class_in_gtt": same, "suggested_gtt": hint, "condition": condition_text(r),
                     "in_crt": crt is not None and key in crt.get(r["kind"], {}),
                     "crt_definition": (crt or {}).get(r["kind"], {}).get(key),
                     # its row states (common/common_helpers/component_class_mapping.row_states), whose definition
                     # changed if it is stale, and what it shares its translation with
                     "states": row_states(r, crt, gtt_now, repeated=r["_line"] in extra, same_in_gtt=same,
                                          suggested=hint, shared=shared.get(r["_line"], [])),
                     "stale_in": stale_in(r, crt, gtt_now), "sharing": shared.get(r["_line"], []),
                     "example": examples.get(key) if r["kind"] == "predicate" else None})
    return {"found": True, "file": f"annotations/{MAPPING_PATH.name}", "schema_found": SCHEMA_USED.exists(),
            "rows": rows, "none": NONE, "repeats": repeated, "checked_values": list(CHECKED),
            # the names the page compares with: each row state (ROW_STATES) and whose definition changed (stale_in)
            "state_names": {"REPEATED": REPEATED, "STALE": STALE, "MISSING_TARGET": MISSING_TARGET,
                            "NOW_EXISTS": NOW_EXISTS, "SUGGESTED": SUGGESTED, "SHARED": SHARED},
            "stale_in_names": {"IN_CRT": IN_CRT, "IN_GTT": IN_GTT},
            "gtt": {kind: [{"component_class": n, "definition": d} for n, d in sorted(names.items())]
                    for kind, names in gtt.items()}}


def save_mapping(data: Data, sent: list) -> None:
    """Write the person's choices for the rows the page showed. The rows'
    kinds and component classes of the current schema must still be the file's
    first rows, in order; rows added after them (by step 070) are kept as
    they are. A row saved as checked stores the current schema's definition
    of its component class and the ground truth schema's definition of its
    component class of the ground truth schema, unless the page says
    keep_definition: a stale row the person hasn't ticked again keeps its
    checked value and its old definitions, so it stays stale."""
    rows = read_mapping(MAPPING_PATH)
    crt = _crt()
    if [(r["kind"], r["component_class_from_past_or_crt_schema"]) for r in rows[:len(sent)]] != \
            [(r.get("kind"), r.get("component_class_from_past_or_crt_schema")) for r in sent]:
        raise ValueError(f"annotations/{MAPPING_PATH.name} has changed since the page was loaded (step 070 or a "
                         f"hand edit), so saving could overwrite it: reload the page, then make your last change "
                         f"again.")
    vocab = _gtt(data)
    gtt_now = _gtt_definitions(vocab)
    gtt = {kind: {component_class_key(n): n for n in names} for kind, names in vocab.items()}
    coined = None
    for row, s in zip(rows, sent):
        name = str(s.get("component_class_in_gtt") or "").strip()
        if name != NONE and component_class_key(name) not in gtt.get(row["kind"], {}):
            if name == row["component_class_in_gtt"]:
                pass                                   # a missing target left as it is: kept, and still marked
            else:
                coined = _coined(data) if coined is None else coined
                a = 'an' if row['kind'] == 'entity class' else 'a'
                raise ValueError(
                    f"\"{name}\" isn't {a} {row['kind']} of the ground truth schema "
                    f"(annotations/{GROUND_TRUTH_SCHEMA.name})"
                    + (", only coined (used in the ground truth): add it to the ground truth schema first (view "
                       "Ground truth schema), then pick it here" if component_class_key(name) in coined[row["kind"]]
                       else ", so nothing can translate to it. Pick one from the list, or " + NONE)
                    + ". Nothing was saved.")
        elif name != NONE:
            name = gtt[row["kind"]][component_class_key(name)]
        row["component_class_in_gtt"] = name
        swap = row["kind"] == "predicate" and s.get("swap_subject_and_object") == "yes"
        row["swap_subject_and_object"] = "yes" if swap else "no"
        checked = str(s.get("checked") or "no")
        row["checked"] = checked if checked in MAPPING_VALUES["checked"] else "no"
        if row["checked"] == "same component class" and (name == NONE or component_class_key(name) !=
                                                          component_class_key(row["component_class_from_past_or_crt_schema"])):
            row["checked"] = "no"                      # changed by hand: no longer the same spelling, so it needs checking
        if is_checked(row) and not s.get("keep_definition"):
            if crt is not None:
                row["definition_from_past_or_crt_schema"] = \
                    crt.get(row["kind"], {}).get(component_class_key(row["component_class_from_past_or_crt_schema"]), "")
            row["definition_in_gtt"] = gtt_definition(row, gtt_now)
    write_csv(MAPPING_PATH, MAPPING_COLUMNS, rows)


def delete_mapping_row(line: int, kind: str, name: str) -> None:
    """Delete one row, only if it is one of a component class's repeated rows and is
    still at that line (so nothing else can be deleted, even by mistake)."""
    rows = read_mapping(MAPPING_PATH)
    target = next((r for r in rows if r["_line"] == line), None)
    if target is None or (target["kind"], target["component_class_from_past_or_crt_schema"]) != (kind, name):
        raise ValueError(f"annotations/{MAPPING_PATH.name} has changed since the page was loaded (step 070 or a "
                         f"hand edit), so the row to delete can't be told for sure: reload the page, then delete it "
                         f"again.")
    if not any(line in r["lines"] for r in repeats(rows)):
        raise ValueError("only a component class's repeated rows can be deleted here, so that no translation is lost. "
                         "To delete another row, edit annotations/component_class_mapping.csv by hand.")
    write_csv(MAPPING_PATH, MAPPING_COLUMNS, [r for r in rows if r is not target])


# --------------------------------------------------------------------------
# help
# --------------------------------------------------------------------------

def _plain(markdown: str) -> str:
    """Markdown as plain text, for a tooltip: links become their words; bold, italics, and code marks go."""
    text = re.sub(r"\[([^\[\]]+)\]\([^()\s]+\)", r"\1", markdown)
    return re.sub(r"\*\*|(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)|`", "", text).strip()


def terms() -> dict:
    """{term, lower case: its definition, as plain text}, from docs/terminology.md: every name written in bold in the
    first cell of a row of its tables (a term and its other names), read from the file each time."""
    rows = [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in TERMINOLOGY.read_text(encoding="utf-8").splitlines() if line.startswith("| **")]
    rows = [r for r in rows if len(r) >= 2]
    out = {}
    # A row's own names first; then the names a definition writes in bold ("its **pool position**"), which that row
    # defines too, unless another row is theirs.
    for cell in (0, 1):
        for r in rows:
            for name in re.findall(r"\*\*([^*]+)\*\*", r[cell]):
                out.setdefault(_plain(name).lower(), _plain(r[1]))
    return out


def doc_text(path: str) -> dict:
    """A Markdown file of the repository, for the page to show when its link is followed: only a .md file inside the
    repository folder (never anything else on the computer)."""
    target = (ROOT / path).resolve()
    if target.suffix.lower() != ".md" or not target.is_relative_to(ROOT.resolve()) or not target.is_file():
        raise ValueError(f"{path} isn't a Markdown file of this repository, so it can't be shown here")
    return {"file": target.relative_to(ROOT.resolve()).as_posix(), "markdown": target.read_text(encoding="utf-8")}


def _section(text: str, head: str) -> str:
    """The README's section under `head`, as Markdown: from the heading to the next heading."""
    i = text.index(head)
    nxt = [j for j in (text.find("\n## ", i + len(head)), text.find("\n### ", i + len(head))) if j != -1]
    return text[i:min(nxt) if nxt else len(text)].strip()


def help_text(view: str) -> dict:
    """The README's section for a view, as Markdown; for Ground truth, followed by the two lists of what the tool
    can and can't do (HELP_ALSO)."""
    head = HELP_SECTIONS.get(view)
    if head is None:
        raise ValueError(f"no help for {view!r}")
    text = README.read_text(encoding="utf-8")
    section = _section(text, head)
    whole = "\n\n".join([section] + [_section(text, h) for h in HELP_ALSO.get(view, ())])
    # The section's first paragraph after its heading: what the view is for, shown at the top of the view.
    paragraphs = [p.strip() for p in section[len(head):].split("\n\n") if p.strip()]
    return {"file": f"annotations/{README.name}", "markdown": whole, "intro": paragraphs[0] if paragraphs else ""}


# --------------------------------------------------------------------------
# reviewers' comments
# --------------------------------------------------------------------------

def reviewer_comments_view() -> dict:
    """The comments subject-matter experts sent back from the review page (helpers/review_page.md), read from
    annotations/reviews/ the same way py helpers/review_page.py --read reads them
    (common/common_helpers/review_comments.read_all): each with its state against the files now. Read-only."""
    read = read_reviewer_comments([REVIEWER_COMMENTS_DIR], GROUND_TRUTH_SCHEMA, MAPPING_PATH)
    return {"folder": f"annotations/{REVIEWER_COMMENTS_DIR.name}/", "files": [f.name for f in read["files"]],
            "problems": read["problems"], "comments": read["comments"], "not_verified": NOT_VERIFIED,
            # each topic and its heading, in order, and the states the page filters by
            # (common/common_helpers/review_comments.py)
            "headings": list(TOPIC_HEADINGS.items()),
            "states": {"CHANGED": CHANGED, "UNCHANGED": UNCHANGED, "GONE": GONE}}


def expert_questions_view() -> dict:
    """The questions for subject-matter experts (annotations/questions_for_experts.md, read by
    common/common_helpers/expert_questions.read_questions), each with what its answer may change (its Affects), so
    the tool can show, on a record, the questions about it. Read-only; a file not in its format is a problem."""
    try:
        questions = read_questions(QUESTIONS_PATH)
    except ValueError as e:
        return {"file": f"annotations/{QUESTIONS_PATH.name}", "questions": [], "problem": str(e)}
    keep = ("id", "title", "status", "priority", "question_kind", "in_short", "affects")
    return {"file": f"annotations/{QUESTIONS_PATH.name}", "questions": [{k: q[k] for k in keep} for q in questions],
            "problem": "", "open": OPEN}


def left_out_view() -> dict:
    """What the ground truth leaves out on purpose (annotations/left_out.md, read by
    common/common_helpers/left_out.read_left_out), one section per record, for the record view's folded section and
    the Left out view. Read-only; a file not in its format is a problem (the line is named), shown instead of items."""
    file = f"annotations/{LEFT_OUT_PATH.name}"
    try:
        sections = read_left_out(LEFT_OUT_PATH)
    except (ValueError, OSError) as e:
        return {"file": file, "sections": [], "rules": [], "problem": str(e)}
    for sec in sections:
        for it in sec["items"]:
            it["rule_ref"] = rule_ref(it)
    rules = sorted({it["rule_ref"] for sec in sections for it in sec["items"]} - {NO_RULE})
    if any(it["rule_ref"] == NO_RULE for sec in sections for it in sec["items"]):
        rules.append(NO_RULE)
    return {"file": file, "sections": sections, "rules": rules, "no_rule": NO_RULE, "problem": ""}


# --------------------------------------------------------------------------
# schema additions
# --------------------------------------------------------------------------

def _additions() -> tuple:
    """(entries, unread lines) of the additions file (common/common_helpers/schema_io.additions_entries)."""
    return additions_entries(ADDITIONS)


def additions_view(data: Data) -> dict:
    entries, unread = _additions()
    used = {}
    if SCHEMA_USED.exists():
        for kind, key in KIND_KEYS.items():
            used[kind] = {component_class_key(e["component_class"]): e["component_class"]
                          for e in json.loads(SCHEMA_USED.read_text(encoding="utf-8")).get(key, [])
                          if e.get("from") != "additions"}
    names = []
    if EXTRACTION_DETAILS.exists():
        details = json.loads(EXTRACTION_DETAILS.read_text(encoding="utf-8"))
        have = {(e["entry_type"], component_class_key(e["component_class"])) for e in entries if e["entry_type"] != "pattern"}
        names = [{**n, "added": (n["kind"], component_class_key(n["component_class"])) in have}
                 for n in (details.get("new_component_classes") or {}).get("component_classes", [])]
    return {"file": f"annotations/{ADDITIONS.name}", "entries": entries, "unread": unread,
            "new_component_classes": names, "counted_over": (json.loads(EXTRACTION_DETAILS.read_text(encoding="utf-8"))
                                             .get("new_component_classes") or {}).get("counted_over")
            if EXTRACTION_DETAILS.exists() else None,
            "schema_component_classes": {k: sorted(v.values()) for k, v in used.items()}}


def check_addition(data: Data, e: dict) -> str | None:
    """What's wrong with one entry, or None (common/common_helpers/schema_io.addition_problem)."""
    return addition_problem(e, {data.positions[i]: part for i, part in data.parts.items() if i in data.positions})


def save_additions(data: Data, entries: list) -> None:
    """Rewrite the additions file with these entries, keeping its comments."""
    _, unread = _additions()
    if unread:
        raise ValueError(f"annotations/{ADDITIONS.name} has line(s) its layout can't read "
                         f"({'; '.join(unread[:3])}), so saving here would lose them. Fix them by hand in a text "
                         f"editor first.")
    seen = set()
    clean = []
    for e in entries:
        problem = check_addition(data, e)
        if problem:
            raise ValueError(problem)
        if e["entry_type"] == "pattern":
            triple = tuple(str(e[k]).strip() for k in ("subject_class", "predicate", "object_class"))
            key, shown = ("pattern",) + tuple(component_class_key(x) for x in triple), pattern_key(triple)
        else:
            key, shown = (e["entry_type"], component_class_key(e["component_class"])), e["component_class"]
        if key in seen:
            raise ValueError(f"{shown} (additions file) is there twice: delete one of them")
        seen.add(key)
        if e["entry_type"] == "pattern":
            clean.append({"entry_type": "pattern", "subject_class": triple[0], "predicate": triple[1],
                          "object_class": triple[2], "source": " ".join(e["source"].split())})
            continue
        clean.append({"entry_type": e["entry_type"], "component_class": e["component_class"].strip(),
                      "definition": " ".join(e["definition"].split()), "source": " ".join(e["source"].split()),
                      "patterns": [[str(a).strip(), str(b).strip()] for a, b in e.get("patterns") or []]
                      if e["entry_type"] == "predicate" else []})
    write_text(ADDITIONS, additions_text(additions_header(ADDITIONS), clean))


# --------------------------------------------------------------------------
# partial pairs
# --------------------------------------------------------------------------

def _read_reviews_rows() -> list:
    """The file's rows; a verdict read as step 070 reads it (case and spacing aside: partial_reviews.verdict_of)."""
    if not REVIEWS_PATH.exists():
        return []
    with open(REVIEWS_PATH, encoding="utf-8-sig", newline="") as fh:
        rows = [{c: (r.get(c) or "").strip() for c in REVIEW_COLUMNS} for r in csv.DictReader(fh)]
    for r in rows:
        if verdict_of(r) in (SAME, NOT_SAME):
            r["verdict"] = verdict_of(r)
    return rows


def _words(s: str) -> list:
    """s cut into words, each with the spaces after it."""
    return re.findall(r"\S+\s*", s or "")


def pair_differences(row: dict) -> dict:
    """For a pair's subject instances, predicates, and object instances: whether
    the two sides differ once evened out (norm_text, as step 070 compares them),
    and if so each side cut into words, each word marked when only that side has
    it (words compared evened out, in order)."""
    out = {}
    for slot in ("subject", "predicate", "object"):
        gt, tr = row.get(f"ground_truth_{slot}", ""), row.get(f"translated_{slot}", "")
        if norm_text(gt) == norm_text(tr):
            out[slot] = None
            continue
        a, b = _words(gt), _words(tr)
        sides = [[[w, True] for w in a], [[w, True] for w in b]]
        match = difflib.SequenceMatcher(None, [norm_text(w) for w in a], [norm_text(w) for w in b], autojunk=False)
        for i, j, n in match.get_matching_blocks():
            for k in range(n):
                sides[0][i + k][1] = sides[1][j + k][1] = False
        out[slot] = {"ground_truth": sides[0], "translated": sides[1]}
    return out


def partial_view(data: Data) -> dict:
    """Evaluation's last run's partial pairs of tuning records, plus pairs
    ruled out by an earlier review (no longer paired, so not in compared_triples.csv),
    each with the verdict so far and the record's title, position, and text.
    When the pair's translated extracted triple has multiplicity above 1 in
    its record's multiset of translated extracted triples, "occurrences" lists
    every occurrence: the extracted triple (current schema) that translates
    to it, what step 070 made of it (its status in compared_triples.csv), and
    whether it is the one in this pair. "differences" is pair_differences.
    Read from compared_triples.csv (one row per occurrence); step 070 itself
    is not changed."""
    reviews = {row_key(r): r["verdict"] for r in _read_reviews_rows()}
    items, seen = [], set()
    rows = []
    if COMPARED.exists():
        with open(COMPARED, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    # a record's occurrences, by their translated extracted triple as written (two that read the same are one element)
    by_triple = collections.defaultdict(list)
    for r in rows:
        if r.get("status") != GROUND_TRUTH_ONLY:
            by_triple[(r["record_id"],) + tuple(r.get(f"translated_{k}", "") for k in OCCURRENCE)].append(r)

    def occurrences(row: dict) -> list | None:
        if "translated_subject_class" in row:            # a pair in compared_triples.csv: its whole triple
            same = by_triple.get((row["record_id"],) + tuple(row.get(f"translated_{k}", "") for k in OCCURRENCE), [])
        else:                                            # a ruled-out pair: its entity classes are unknown, so only if unambiguous
            keys = [k for k in by_triple if k[0] == row["record_id"] and
                    [k[1 + OCCURRENCE.index(s)] for s in ("subject", "predicate", "object")] ==
                    [row.get(f"translated_{s}", "") for s in ("subject", "predicate", "object")]]
            same = by_triple[keys[0]] if len(keys) == 1 else []
        if len(same) < 2:
            return None
        return [{"extracted": {k: o.get(f"extracted_{k}", "") for k in OCCURRENCE}, "status": o.get("status", ""),
                 "this": o is row} for o in same]

    def add(row: dict, verdict):
        rid = row["record_id"]
        if data.parts.get(rid) != TUNING or row_key(row) in seen:
            return
        seen.add(row_key(row))
        record = data.records.get(rid) or {}
        items.append({**{c: row.get(c, "") for c in REVIEW_COLUMNS if c != "verdict"},
                      "verdict": verdict, "position": data.positions.get(rid),
                      "title": record.get("title") or rid,
                      "text": full_text(record) if record else None, "occurrences": occurrences(row),
                      "differences": pair_differences(row)})

    for r in rows:
        if r.get("status") == PARTIAL_PAIR:
            add(r, reviews.get(row_key(r)))
    for r in _read_reviews_rows():
        if r["verdict"] == NOT_SAME:
            add(r, NOT_SAME)
    return {"found": COMPARED.exists(), "file": f"annotations/{REVIEWS_PATH.name}", "items": items,
            # the statuses the page names an occurrence by (common/common_helpers/partial_reviews.py)
            "statuses": {"EXTRACTED_ONLY": EXTRACTED_ONLY, "PAIRS": [EXACT_PAIR, PARTIAL_PAIR]}}


def save_review(data: Data, item: dict) -> None:
    """File a verdict ("same fact", "not the same fact", or "" to take one
    back) for one pair of a tuning record, replacing any earlier one."""
    if data.parts.get(item.get("record_id")) != TUNING:
        raise ValueError("only tuning records' pairs can be reviewed (held-out results stay unseen)")
    verdict = item.get("verdict") or ""
    if verdict not in (SAME, NOT_SAME, ""):
        raise ValueError(f"verdict must be '{SAME}' or '{NOT_SAME}'")
    row = {c: str(item.get(c) or "").strip() for c in REVIEW_COLUMNS}
    rows = [r for r in _read_reviews_rows() if row_key(r) != row_key(row)]
    if verdict:
        rows.append(row)
    write_csv(REVIEWS_PATH, REVIEW_COLUMNS, rows)


# --------------------------------------------------------------------------
# the ground truth schema: definitions, renaming, merging
# --------------------------------------------------------------------------
# A rename or merge changes several of the person's files at once. plan_vocab
# works out every file's new content without writing anything, so the page
# can show what would change; apply_vocab works it out again (never trusting
# the page) and writes all the files, putting every one back if any write
# fails.

#: Component classes written by code, never renamed here.
FIXED = {component_class_key(n) for n in (ENTRY_CLASS, ENTRY_PREDICATE, UNDECIDED)}
#: The ground truth files' columns that hold each kind of component class.
GT_COLUMNS = {"entity class": ("subject_class", "object_class"), "predicate": ("predicate",)}


def vocab_view(data: Data) -> dict:
    """Every component class of the ground truth schema, by kind: its
    definition (empty if coined and not yet in the ground truth schema), how many
    ground truth triples and describes triples, and files, use it, and how many rows of the translation
    table translate to it."""
    data.read_hand()                                   # the file as it is now: it may have been edited by hand
    gt = read_ground_truth()
    vocab = with_coined(data.hand, gt)
    table = read_mapping(MAPPING_PATH) if MAPPING_PATH.exists() else []
    files = {}
    for p in sorted(GROUND_TRUTH_DIR.glob(PATTERN)):
        for r in _read_rows(p):
            for kind, columns in GT_COLUMNS.items():
                for c in columns:
                    files.setdefault((kind, component_class_key(r.get(c))), set()).add(p.name)
    out = {}
    for kind, key in KIND_KEYS.items():
        coined = {component_class_key(n) for n in vocab["coined"][key]}
        out[kind] = [{"component_class": n, "definition": d or "", "in_hand": component_class_key(n) not in coined,
                      "uses": len(uses_of(gt, kind, n)),
                      "files": sorted(files.get((kind, component_class_key(n)), [])),
                      "translated_from": [r["component_class_from_past_or_crt_schema"] for r in table
                                          if r["kind"] == kind and component_class_key(r["component_class_in_gtt"]) == component_class_key(n)],
                      # a predicate's patterns, for the page's overview: [[subject class, object class], ...]
                      "patterns": [[s, o] for s, p, o in vocab["patterns"]
                                   if kind == "predicate" and component_class_key(p) == component_class_key(n)]}
                     for n, d in sorted(vocab[key].items(), key=lambda kv: kv[0].lower())]
    return {"file": f"annotations/{GROUND_TRUTH_SCHEMA.name}", "vocabulary": out}


def _csv_bytes(columns: list, rows: list) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _plan(data: Data, kind: str, old: str, new: str) -> tuple:
    """(what the page is shown, {path: new bytes}) for renaming `old` to `new`,
    or merging `old` into `new` when `new` is already in the ground truth
    schema or coined in the ground truth."""
    if kind not in KIND_KEYS:
        raise ValueError("kind must be entity class or predicate")
    old, new = str(old or "").strip(), str(new or "").strip()
    data.read_hand()                                   # the file as it is now: it may have been edited by hand
    gt = read_ground_truth()
    vocab = with_coined(data.hand, gt)[KIND_KEYS[kind]]
    spelled = {component_class_key(n): n for n in vocab}
    if component_class_key(old) not in spelled:
        raise ValueError(f"{old} isn't {'an entity class' if kind == 'entity class' else 'a predicate'} of the ground "
                         f"truth schema, nor coined in the ground truth, so it can't be renamed or merged: reload the "
                         f"page to see the ground truth schema as it is now.")
    old = spelled[component_class_key(old)]
    if component_class_key(old) in FIXED or component_class_key(new) in FIXED:
        raise ValueError("CatalogEntry, DESCRIBES, and X are written by code (the describes triple), so they can't be "
                         "renamed, merged, or used as a new component class")
    if new == old:
        raise ValueError("the new component class is the same as the old one: nothing to change. Type another one")
    merging = component_class_key(new) in spelled and component_class_key(new) != component_class_key(old)
    target = spelled[component_class_key(new)] if merging else new
    if not component_class_key(target) or any(c.isspace() for c in target) or target.startswith("#") \
            or ";" in target or "->" in target:
        raise ValueError("the new " + ONE_WORD[4:])
    k = component_class_key(old)
    files, changes, notes = {}, [], []

    # 1. the ground truth files: every cell holding the component class, in any spelling
    for p in sorted(GROUND_TRUTH_DIR.glob(PATTERN)):
        with open(p, encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            columns, rows = list(reader.fieldnames or []), list(reader)
        cells = 0
        for r in rows:
            for c in GT_COLUMNS[kind]:
                if c in r and component_class_key(r[c]) == k:
                    r[c], cells = target, cells + 1
        if cells:
            files[p] = _csv_bytes(columns, rows)
            changes.append({"file": f"annotations/ground_truth/{p.name}", "what": f"{cells} cell(s): {old} → {target}"})
    # 2. the ground truth schema
    hand_bytes, how = rename_in_ground_truth_schema(GROUND_TRUTH_SCHEMA, kind, old, target)
    if how != "unchanged":
        files[GROUND_TRUTH_SCHEMA] = hand_bytes
        changes.append({"file": f"annotations/{GROUND_TRUTH_SCHEMA.name}", "what": {
            "renamed": f"the entry {old} renamed {target}, and every pattern naming it",
            "merged": f"the entry {old} deleted (its definition and source line too); every pattern naming it now "
                      f"names {target}" + ("; its patterns moved under " + target if kind == "predicate" else ""),
            "patterns only": f"every pattern naming {old} now names {target}"}[how]})
    # 3. the translation table: rows translating to the component class
    if MAPPING_PATH.exists():
        table = read_mapping(MAPPING_PATH)
        hit = [r for r in table if r["kind"] == kind and component_class_key(r["component_class_in_gtt"]) == k]
        if hit:
            new_hand = gtt_definitions(read_schema_bytes(hand_bytes))      # the file's own, as step 070 reads it
            for r in hit:
                r["component_class_in_gtt"] = target
            stale = [r["component_class_from_past_or_crt_schema"] for r in hit
                     if is_checked(r) and is_stale_gtt(r, new_hand)]
            gone = [r["component_class_from_past_or_crt_schema"] for r in hit if is_missing_target(r, new_hand)]
            if gone:
                notes.append(f"{len(gone)} row(s) of the translation table will then have a missing target, since "
                             f"{target} is coined, not in the ground truth schema: {', '.join(gone)} (current or past "
                             f"schema). Add {target} to the ground truth schema, or pick another component class "
                             f"for them: press Translation table at the top of this page.")
            files[MAPPING_PATH] = _csv_bytes(MAPPING_COLUMNS, table)
            changes.append({"file": f"annotations/{MAPPING_PATH.name}",
                            "what": f"{len(hit)} row(s) translating to {old} now translate to {target}"})
            if stale:
                notes.append(f"{len(stale)} row(s) of the translation table will then be stale, since {target}'s "
                             f"definition isn't the one they were checked against: {', '.join(stale)} (current or past "
                             f"schema). Check them again: press Translation table at the top of this page.")
    # 4. partial pair reviews, filed under the predicate's spelling
    if kind == "predicate" and REVIEWS_PATH.exists():
        reviews = _read_reviews_rows()
        cells = 0
        for r in reviews:
            for c in ("ground_truth_predicate", "translated_predicate"):
                if component_class_key(r[c]) == k:
                    r[c], cells = target, cells + 1
        if cells:
            kept, verdicts = [], {}
            for r in reviews:
                key_ = row_key(r)
                if key_ in verdicts:
                    if verdicts[key_] != r["verdict"]:
                        raise ValueError(f"merging {old} into {target} would make two of your partial pair reviews "
                                         f"the same pair with different verdicts (record {r['record_id']}); take "
                                         f"one back first: press Partial pairs at the top of this page")
                    continue
                verdicts[key_] = r["verdict"]
                kept.append(r)
            files[REVIEWS_PATH] = _csv_bytes(REVIEW_COLUMNS, kept)
            changes.append({"file": f"annotations/{REVIEWS_PATH.name}",
                            "what": f"{cells} cell(s): {old} → {target}, so your verdicts still apply"})
    # drafted batches not opened yet are never changed (they're step 050's output)
    unopened = []
    if DRAFTS_DIR.exists():
        opened = {int(m.group(1)) for p in GROUND_TRUTH_DIR.glob(PATTERN) if (m := NUMBERED.fullmatch(p.name))}
        for p in sorted(DRAFTS_DIR.glob(DRAFT_PATTERN)):
            m = DRAFT_NUMBERED.fullmatch(p.name)
            if m and int(m.group(1)) not in opened and any(
                    component_class_key(r.get(c)) == k for r in _read_rows(p) for c in GT_COLUMNS[kind]):
                unopened.append(p.name)
    if unopened:
        notes.append(f"Drafted batch(es) not opened yet still use {old}: {', '.join(unopened)} (step 050's output, never "
                     f"changed here). Once opened, the tool marks {old} there ✖: change it to {target}.")
    if not files:
        raise ValueError(f"nothing uses {old}: there is nothing to change")
    return {"kind": kind, "old": old, "new": target, "merge": merging, "changes": changes, "notes": notes}, files


def plan_vocab(data: Data, item: dict) -> dict:
    refuse_if_held_out(data, item, f"renaming or merging {item.get('old')}")
    with HAND_LOCK:
        return _plan(data, item.get("kind"), item.get("old"), item.get("new"))[0]


def _write_all(files: dict) -> None:
    """Write every file, or none: if a write fails, every file already written is put back."""
    originals = {p: p.read_bytes() for p in files}
    done = []
    try:
        for p, content in files.items():
            tmp = p.with_name(p.name + ".part")
            tmp.write_bytes(content)
            os.replace(tmp, p)
            done.append(p)
    except Exception:
        for p in done:
            p.write_bytes(originals[p])
        raise


def apply_vocab(data: Data, item: dict) -> dict:
    """Rename or merge, as plan_vocab showed (worked out again, then written)."""
    refuse_if_held_out(data, item, f"renaming or merging {item.get('old')}")
    with HAND_LOCK:
        shown, files = _plan(data, item.get("kind"), item.get("old"), item.get("new"))
        _write_all(files)
        data.read_hand()
        return shown


def define_vocab(data: Data, item: dict) -> dict:
    """Change the definition of an entity class or predicate of the ground truth schema."""
    kind, name = item.get("kind"), str(item.get("component_class") or "").strip()
    if kind not in KIND_KEYS:
        raise ValueError("kind must be entity class or predicate")
    refuse_if_held_out(data, item, f"changing the definition of {name}")
    with HAND_LOCK:
        content = redefine_in_ground_truth_schema(GROUND_TRUTH_SCHEMA, kind, name, item.get("definition") or "")
        stale = []
        if MAPPING_PATH.exists():
            now = gtt_definitions(with_coined(read_schema_bytes(content), read_ground_truth()))
            stale = [r["component_class_from_past_or_crt_schema"] for r in read_mapping(MAPPING_PATH)
                     if r["kind"] == kind and component_class_key(r["component_class_in_gtt"]) == component_class_key(name)
                     and is_checked(r) and is_stale_gtt(r, now)]
        _write_all({GROUND_TRUTH_SCHEMA: content})
        data.read_hand()
    return {"saved": True, "stale": stale}


def read_schema_bytes(content: bytes) -> dict:
    """The ground truth schema as it would read with these bytes (written to a temporary file next to it)."""
    tmp = GROUND_TRUTH_SCHEMA.with_name(GROUND_TRUTH_SCHEMA.name + ".read")
    tmp.write_bytes(content)
    try:
        return read_ground_truth_schema(tmp)
    finally:
        tmp.unlink()


# --------------------------------------------------------------------------
# the server
# --------------------------------------------------------------------------

def make_handler(data: Data):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):                    # quiet: the page shows what happened
            pass

        def _send(self, status: int, body: bytes, kind: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, value, status: int = 200) -> None:
            self._send(status, json.dumps(value, ensure_ascii=False).encode("utf-8"),
                       "application/json; charset=utf-8")

        def do_GET(self):
            url = urlsplit(self.path)
            q = parse_qs(url.query)
            try:
                if url.path == "/":
                    self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
                elif url.path.startswith("/fonts/") and url.path.endswith(".woff2") and "/" not in url.path[7:] \
                        and (FONTS / url.path[7:]).is_file():
                    self._send(200, (FONTS / url.path[7:]).read_bytes(), "font/woff2")
                elif url.path == "/api/batches":
                    gt = read_ground_truth()
                    self._json({"batches": list_batches(), "records_found": bool(data.records),
                                "problems": gt.problems, "gaps": ground_truth_schema_gaps(data, gt)})
                elif url.path == "/api/status":
                    # with the levels the page compares with (common/common_helpers/status.py)
                    self._json({**project_status(data.records or None), "levels": {"TO_DO": TO_DO, "LOOK": LOOK}})
                elif url.path == "/api/gaps":
                    self._json(ground_truth_schema_gaps(data, read_ground_truth()))
                elif url.path == "/api/mapping":
                    self._json(mapping_view(data))
                elif url.path == "/api/partial":
                    self._json(partial_view(data))
                elif url.path == "/api/help":
                    self._json(help_text(q["view"][0]))
                elif url.path == "/api/terms":
                    self._json(terms())
                elif url.path == "/api/doc":
                    self._json(doc_text(q["path"][0]))
                elif url.path == "/api/guidelines":
                    self._json({"file": f"annotations/{GUIDELINES.name}", "markdown": GUIDELINES.read_text(encoding="utf-8")})
                elif url.path == "/api/additions":
                    self._json(additions_view(data))
                elif url.path == "/api/vocab":
                    self._json(vocab_view(data))
                elif url.path == "/api/reviewer_comments":
                    self._json(reviewer_comments_view())
                elif url.path == "/api/expert_questions":
                    self._json(expert_questions_view())
                elif url.path == "/api/left_out":
                    self._json(left_out_view())
                elif url.path == "/api/raw_record":
                    rid = q.get("id", [""])[0]
                    raw = saved_copy(data.records[rid], HARVEST) if rid in data.records else None
                    if raw is None:
                        self._json({"error": f"No saved copy from the harvest for the id {rid!r} on this computer."}, 404)
                    else:
                        self._send(200, json.dumps(raw, ensure_ascii=False, indent=2).encode("utf-8"),
                                   "application/json; charset=utf-8")
                elif url.path == "/api/batch":
                    n = int(q["n"][0])
                    self._json(batch_view(data, n, open_batch(n)))
                else:
                    self._json({"error": "not found"}, 404)
            except Exception as e:                          # noqa: BLE001 -- shown on the page
                self._json({"error": str(e)}, 400)

        def do_POST(self):
            url = urlsplit(self.path)
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                if url.path == "/api/save":
                    problems = save_batch(data, int(body["n"]), body["records"])
                    gt = read_ground_truth()
                    self._json({"problems": problems, "patterns": patterns_view(data, gt), **definitions_view(data, gt)})
                elif url.path == "/api/mapping/save":
                    save_mapping(data, body["rows"])
                    # each row's states as saved, by line, for the page to show (it computes none itself)
                    self._json({"saved": True, "rows": {r["_line"]: {k: r[k] for k in ("states", "stale_in", "sharing")}
                                                        for r in mapping_view(data)["rows"]}})
                elif url.path == "/api/additions/save":
                    save_additions(data, body["entries"])
                    self._json({"saved": True})
                elif url.path == "/api/hand/add":
                    self._json({"added": add_to_hand(data, body)})
                elif url.path == "/api/additions/check":
                    self._json({"problem": check_addition(data, body)})
                elif url.path == "/api/partial/review":
                    save_review(data, body)
                    self._json({"saved": True})
                elif url.path == "/api/vocab/plan":
                    self._json(plan_vocab(data, body))
                elif url.path == "/api/vocab/apply":
                    self._json(apply_vocab(data, body))
                elif url.path == "/api/vocab/define":
                    self._json(define_vocab(data, body))
                elif url.path == "/api/mapping/delete":
                    delete_mapping_row(int(body["line"]), body["kind"], body["component_class"])
                    self._json({"deleted": True})
                else:
                    self._json({"error": "not found"}, 404)
            except Exception as e:                          # noqa: BLE001 -- shown on the page
                self._json({"error": str(e)}, 400)
    return Handler


def serve(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(Data()))
