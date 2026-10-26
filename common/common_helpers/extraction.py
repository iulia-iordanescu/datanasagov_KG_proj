"""
common/common_helpers/extraction.py -- what the steps that ask a model for a record's
triple instances (040) or classed triples (050, 060) share: 040 (learning the schema), 050 (drafting ground truth)
and 060 (extracting with a schema), so they all extract the same kind of facts,
and 060 is evaluated against 050 on equal terms.

    rules_for(record)          the shared rules (common/common_prompts/extraction_rules.txt),
                               with the record's field names filled in
    reply(with_classes)        the reply format (common/common_prompts/extraction_reply.txt):
                               each triple with its entity classes (050, 060) or
                               without (040, which learns them in a later stage)
    prompt(...)                a step's prompt filled with all of the above
    wrap(piece)                a text piece between BEGIN/END RECORD lines
    shape_error(reply)         what is wrong with a reply's shape (no "triples" list), or None
    ask_model(...)             one cached model call per text piece; a record
                               with a failed call is left out whole; an answer
                               cut off earlier with the same limit isn't asked again;
                               an answer of the wrong shape (shape_error) is asked again, never kept
    failed_note(replies, where)   the report's warning for those records
    best_copies(...)           one copy of each fact: the first that passed its checks
    build_rows(...)            a record's replies -> checked rows + removed items
                               (050, 060: rows with entity classes)

Each step keeps only what is its own: the top of its prompt (040: no
vocabulary, predicates in the model's own words; 050: a vocabulary to reuse
or extend; 060: only the schema's) and how it chooses records.

What build_rows does with a record's replies (one per text piece):

  1. the describes triple first (common/common_helpers/triples_io.py), with the first describes
     class a reply named ("X" if none did);
  2. every item of every reply's "triples", cleaned by triples_io.clean_triple;
     a reply without a "triples" list, and an item that isn't a JSON object or
     whose subject, predicate, or object is missing, empty, true/false, null, a
     list, or an object (a number is read as text), is removed as "malformed";
  3. every row checked (common/common_helpers/validate.py) against the record's WHOLE
     text: errors (no_source_text, source_not_in_text, describes_*) and
     flags (reworded subject or object instances, component classes not in
     the schema, …);
  4. the same subject, predicate, object, and entity classes again (e.g.
     stated in two pieces): one copy is kept, the first without errors (the
     first copy when every copy has errors; best_copies), and the others are
     removed as "duplicate"; the same triple instance with OTHER entity
     classes is kept, and every such row is flagged conflicting_classes.

Nothing is dropped for an error or a flag: that's for the person (050) or
the step (060) to decide. Terms: docs/terminology.md.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from common import llm
from common.audit import log
from common.cache import NOT_ASKED_AGAIN, Cache, key, needs
from common.chunking import text_fields
from common.prompt_files import fill, load
from common.report import named
from common.text_match import Text
from common.triples_io import (clean_triple, describes_triple, component_class_key, triple_key)
from common.validate import CONFLICTING_CLASSES, SchemaEntries, check_against_schema, check_describes, check_triple_instance

PROMPTS = Path(__file__).resolve().parents[1] / "common_prompts"       # common/common_prompts/
RULES = load(PROMPTS / "extraction_rules.txt")
REPLY = load(PROMPTS / "extraction_reply.txt")
#: The lines around a record in the prompts. Everything before BEGIN_LINE is the same in every request of a run, so
#: 060 sends it for prompt caching (llm._messages).
BEGIN_LINE = "----- BEGIN RECORD -----"
END_LINE = "----- END RECORD -----"
ROW_KEYS = ("subject", "subject_class", "predicate", "object", "object_class", "source_text")


def rules_for(record: dict) -> str:
    return fill(RULES, field_names=", ".join(f'"{n}:"' for n in text_fields(record)))


def reply(with_classes: bool = True) -> str:
    """The reply format, each triple with its entity classes or without."""
    keys = ROW_KEYS if with_classes else ("subject", "predicate", "object", "source_text")
    return fill(REPLY, fields=", ".join(f'"{k}": "..."' for k in keys)).strip()


def prompt(template, schema_text: str, record: dict, piece: str, with_classes: bool = True, **own) -> str:
    """The prompt for one text piece: template (040's, 050's, or 060's) filled
    with the schema (none for 040), this record's rules, the shared reply
    format and the piece; own: the step's own $names, if its template has any
    (060: $list_things_first)."""
    return fill(template, schema=schema_text, rules=rules_for(record), reply=reply(with_classes),
                text=wrap(piece), **own)


def wrap(piece: str) -> str:
    """A text piece as the prompt's $text: any line that copies END_LINE is
    defanged, so the record can't close its own fence."""
    return llm.fence_safe(piece, END_LINE)


#: What is wrong with the shape of a reply about one text piece, or None: it must hold a "triples" list (the reply
#: format, common/common_prompts/extraction_reply.txt). ask_model asks again for a reply of the wrong shape, and never
#: keeps one, so every reply read below has it.
shape_error = needs(triples=list)


def best_copies(items: list, key, failed) -> tuple:
    """(kept, copies): one copy of each key(item), in the order the keys first appear, and the other copies.
    The copy kept is the first that passed its checks (not failed(item)); only when no copy passed, the first
    copy. So a fact stated twice is never lost because its first copy failed a check (a wrong source text) and
    its second didn't. Used by 040 (stage 2) and by build_rows (050, 060)."""
    best, order, copies = {}, [], []
    for item in items:
        k = key(item)
        if k not in best:
            best[k] = item
            order.append(k)
        elif failed(best[k]) and not failed(item):
            copies.append(best[k])
            best[k] = item
        else:
            copies.append(item)
    return [best[k] for k in order], copies


def build_rows(record_id: str, title: str, text: str, replies: list, schema_entries: SchemaEntries) -> tuple:
    """(rows, removed). rows: the describes triple, then one per triple
    instance, each {"id", ROW_KEYS…, "errors": [...], "flags": [...]}.
    removed: {"reason": "malformed" | "duplicate", "raw" or the row}."""
    removed = []
    named = [str(r.get("describes_class") or "").strip() for r in replies if isinstance(r, dict)]
    head = describes_triple(record_id, title, next((c for c in named if c), ""))
    errors, flags = check_describes(head, record_id, schema_entries)
    rows = [{**head, "errors": errors, "flags": flags}]

    whole = Text(text)
    checked = []
    for reply in replies:
        if not isinstance(reply, dict) or shape_error(reply):
            removed.append({"reason": "malformed", "raw": json.dumps(reply, ensure_ascii=False)})
            continue
        for item in reply["triples"]:
            t = clean_triple(item)
            if t is None:
                removed.append({"reason": "malformed", "raw": json.dumps(item, ensure_ascii=False)})
                continue
            row = {"id": record_id, **{k: t.get(k, "") for k in ROW_KEYS}}
            errors, flags = check_triple_instance(row, whole, title)
            checked.append({**row, "errors": errors, "flags": flags + check_against_schema(row, schema_entries)})

    def copy_key(row):                          # the same triple instance with the same entity classes
        return triple_key(row), component_class_key(row["subject_class"]), component_class_key(row["object_class"])
    kept, copies = best_copies(checked, copy_key, lambda row: bool(row["errors"]))
    removed += [{"reason": "duplicate", **{k: v for k, v in row.items() if k not in ("errors", "flags")}}
                for row in copies]
    pairs = {}                                  # triple key -> {entity class pairs} among the rows kept
    for row in kept:
        pairs.setdefault(triple_key(row), set()).add(copy_key(row)[1:])
    for row in kept:                            # same triple instance, other entity classes
        if len(pairs[triple_key(row)]) > 1:
            row["flags"].append(CONFLICTING_CLASSES)
    rows += kept
    return rows, removed


# --------------------------------------------------------------------------
# asking the model, one call per text piece (040, 050, 060)
# --------------------------------------------------------------------------

@dataclass
class Replies:
    of: dict = field(default_factory=dict)        # {id: [reply per piece]} for records fully answered
    failed: dict = field(default_factory=dict)    # {id: why}
    cut_off: dict = field(default_factory=dict)   # {id: the service's usage} of the failed ones that were cut off
    calls: int = 0                                # model calls made
    reused: int = 0                               # pieces answered from the cache
    cut_reused: int = 0                           # pieces cut off in an earlier run, not asked again


def ask_model(items: list, prompt_for, calls, workers: int, stage: str, plan: str, verb: str,
              cache_until: str | None = None) -> Replies:
    """One model call per text piece of each item ({"id", "pieces", …}),
    prompt_for(item, piece) giving the prompt. Every answer is kept in
    cache/<stage>.json (common/common_helpers/cache.py) the moment it arrives, so a rerun
    pays only for what it doesn't have. A record with any failed call is
    left out of `of`, never half answered; the next run asks it again, unless
    the answer was cut off at the length limit: that is kept too
    (common/common_helpers/cache.py, Cache.cut_off), and a rerun with the same
    limit reuses the failure instead of paying for the same cut. A reply
    without its "triples" list (shape_error) is asked once more, then fails;
    one kept by an earlier run is asked again (common/common_helpers/cache.py, Cache.get).
    plan is the confirmation's first words ("050 will draft 10 record(s)
    into drafted batch 3"); verb names the work in the log ("drafting")."""
    cache = Cache(calls.cache_dir, stage)
    answers, todo, cut_before = {}, {}, {}
    for item in items:
        for i, piece in enumerate(item["pieces"]):
            prompt = prompt_for(item, piece)
            k = key(prompt)
            stored = cache.get(k, shape_error)
            cut = cache.cut_off(k) if stored is None else None
            if stored is not None:
                answers[(item["id"], i)] = stored
            elif cut:
                cut_before[(item["id"], i)] = (cut, cache.cut_off_usage(k))
            else:
                todo[(item["id"], i)] = (k, prompt)

    result = Replies(reused=len(answers), cut_reused=len(cut_before))
    for (rid, i), (why, usage) in cut_before.items():
        result.failed[rid] = f"piece {i + 1}: {why} {NOT_ASKED_AGAIN}"
        result.cut_off[rid] = usage
    if cut_before:
        log.info(f"  {len(cut_before)} text piece(s) were cut off at the answer length limit in an earlier run with "
                 f"the same settings, so they aren't asked again (the report's warnings say what to change)")
    if todo:
        n_records = len({rid for rid, _ in todo})
        calls.paid.start(f"  {plan}: {len(todo)} model call(s) for {n_records} record(s)"
                         + (f", {len(answers)} text piece(s) answered from the cache" if answers else ""))
        before = calls.paid.made
        calls.paid.expect(len(todo))

        def ask(k, prompt):
            reply = llm.call_llm_json(prompt, cache_until=cache_until, check=shape_error)
            calls.paid.made_call()
            return k, reply

        def handle(n, where, answer, error):
            at = {"stage": stage, "record": where[0], "text_piece": where[1] + 1}
            if error is not None:
                result.failed[where[0]] = f"piece {where[1] + 1}: {error}"
                if isinstance(error, llm.CutOff):
                    cache.put_cut_off(todo[where][0], error)
                    result.cut_off[where[0]] = getattr(error, "usage", None) or {}
                log.warning(f"{verb} failed for {where[0]} piece {where[1] + 1}: {error}")
                calls.paid.outcome(at, todo[where][1], error)
                return
            k, reply = answer
            answers[where] = reply
            cache.put(k, reply)
            log.debug(f"{verb} {where[0]} piece {where[1] + 1} ({n}/{len(todo)})")
            calls.paid.outcome(at, todo[where][1])

        llm.run_parallel(ask, dict(todo), workers, handle,
                         "Answers already received are kept in the cache; nothing else was written. Run the step "
                         "again to ask the rest: the answers already received are reused, not paid for again.",
                         not_sent=lambda keys: calls.paid.not_sent(
                             [({"stage": stage, "record": w[0], "text_piece": w[1] + 1}, todo[w][1]) for w in keys]))
        result.calls = calls.paid.made - before

    for item in items:
        replies = [answers.get((item["id"], i)) for i in range(len(item["pieces"]))]
        if item["id"] not in result.failed and all(r is not None for r in replies):
            result.of[item["id"]] = replies
    log.info(f"  {len(result.of)} record(s) answered, {len(result.failed)} failed "
             f"({result.calls} calls, {result.reused} text piece(s) from the cache"
             + (f", {result.cut_reused} cut off in an earlier run" if result.cut_reused else "") + ")")
    return result


def failed_note(replies: Replies, where: str) -> str | None:
    """The warning for the records ask_model left out, with why, or None.
    where: what they are missing from ("the drafted batch", "the output", …)."""
    if not replies.failed:
        return None
    cut = len(replies.cut_off)
    usage = max(replies.cut_off.values(), key=llm.reasoning_tokens) if cut else None
    file = llm.OUTCOMES["file"]
    return (f"{len(replies.failed)} record(s) failed: a model call for one of their text pieces failed, so each "
            f"is left out of {where} whole ({named([f'{i}: {why}' for i, why in replies.failed.items()], 3, '; ')}). "
            + (f"Each failed call of this run is described in {file}. " if file else "")
            + ("Run the step again: only the failed pieces are asked again; every answer already paid for is reused."
               if cut < len(replies.failed) else "")
            + (f"{' But' if cut < len(replies.failed) else ''} {cut} of them had their answer cut off at the answer "
               f"length limit, which a rerun with the same settings would only repeat, so it doesn't ask them again: "
               f"{llm.cut_off_advice(usage)} (docs/running_on_nasa_laptop.md, section 7)." if cut else "")).strip()
