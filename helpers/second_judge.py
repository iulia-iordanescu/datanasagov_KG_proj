"""
second_judge · A blind second judge, from another maker, of my decisions on model output.

Two kinds of my decisions in annotations/ judge what a model wrote: the second opinion's facts the ground truth lacks
(drafted by gemini-4-argon) and the partial pairs (extracted by claude-opus-5-5). One rater's decisions may lean the
way of the models whose output they judge, and a model asked to judge tends to favor output like its own (the
self-preference bias), so the second rater is a model from another maker than both, which sees everything a decision
was made from but never the decision: their agreement measures how far an independent reader reaches the same
decisions (Artstein & Poesio 2008, "Inter-Coder Agreement for Computational Linguistics", Computational Linguistics
34(4)). Two tasks, each judged and reported on its own:

    facts           each reviewed row of annotations/second_opinion_candidates.csv (a fact the second opinion's draft
                    proposed and the ground truth lacked): added, left out (a rule) or already in the ground truth in
                    other words, with the rule of annotations/guidelines.md the judge relies on. It sees the record's
                    text, the candidate and its source text, the annotation guidelines as the annotator reads them,
                    the ground truth schema (as step 050 shows it), and the record's ground truth triples.
    partial pairs   each verdict on a partial pair, in annotations/partial_pairs_to_review.csv or, once moved, in
                    annotations/partial_pair_reviews.csv (one item per pair, by the key the verdicts are filed
                    under): same fact or not the same fact, from the record's text, with the definitions of
                    070_evaluate/metrics/pairs.md quoted. Both triples are shown as the key holds them, subject
                    PREDICATE object, without entity classes (the reviews file has none), whichever file a row is in.

    py helpers/second_judge.py                              judge both tasks (asks once before paying), report
    py helpers/second_judge.py --tasks facts                one task only (facts or partial_pairs)
    py helpers/second_judge.py --ground_truth_at <commit>   the facts task shows the ground truth as it was at that
                                                            Git commit (before the decisions changed it)
    py helpers/second_judge.py --model <name>               another judge (the default: SECOND_JUDGE_MODEL, below)

Only rows that already have our label are judged (a filled decision or verdict): a judge's label seen before
deciding would shape ours. The judge's labels go to annotations/second_judge.csv (one row per judged item and model;
a rerun replaces that model's rows of the tasks it judged). The report gives, per task, the raw agreement with our
labels, the agreement per label, Cohen's kappa, and every disagreement. It runs in the frame every step runs in
(common/common_helpers/step.py, run_step): run id, log, report, manifest, and the answers cached in its own output
folder, so a rerun pays nothing.

Reads:   records.jsonl (020), splits.json (030), annotations/ground_truth_schema.txt, annotations/ground_truth/,
         annotations/guidelines.md, annotations/second_opinion_candidates.csv, annotations/partial_pairs_to_review.csv,
         annotations/partial_pair_reviews.csv
Writes:  second_judge_details.json; annotations/second_judge.csv
Details: helpers/second_judge.md
"""
from __future__ import annotations

import collections
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))                                                  # the repository folder, for common/

from common import llm                                                         # noqa: E402
from common.audit import log                                                   # noqa: E402
from common.cache import Cache, key as cache_key                               # noqa: E402
from common.expert_questions import guideline_rules                            # noqa: E402
from common.files import read_csv_table, read_text, write_csv, write_json      # noqa: E402
from common.ground_truth import ANNOTATED, DRAFTED_BY, NUMBERED, read_ground_truth        # noqa: E402
from common.partial_reviews import (NOT_SAME, SAME, pair_text, read_reviews, review_conflicts, row_key,  # noqa: E402
                                    verdict_of)
from common.prompt_files import fill, load                                     # noqa: E402
from common.records_io import full_text                                        # noqa: E402
from common.report import cell, model_calls, named                             # noqa: E402
from common.second_opinion import ADDED, IN_OTHER_WORDS, TRIPLE, candidate_key, read_candidates  # noqa: E402
from common.step import ANNOTATIONS_DIR, Results, Spec, check_settings, load_moves, repo_path, run_step  # noqa: E402
from common.stop import Stop                                                   # noqa: E402

STEP = "second_judge"
COMMAND, GUIDE = "py helpers/second_judge.py", "helpers/second_judge.md"
#: The default judge: OpenAI's flagship, gpt-6-astra (released 2026-09-03), from another maker than the extraction
#: model (claude-opus-5-5, Anthropic) and than the second opinion's (gemini-4-argon, Google). Its settings follow
#: common/common_helpers/llm.py's rules for OpenAI's GPT-6 models (no temperature; `reasoning_effort`;
#: `max_completion_tokens`), each verified in OpenAI's docs. A setting (--model): gpt-6.1-sol is the fallback.
SECOND_JUDGE_MODEL = "gpt-6-astra"

PROMPTS_DIR = Path(__file__).resolve().parent / "helpers_prompts"
FACTS_PROMPT = load(PROMPTS_DIR / "second_judge_facts.txt")
PAIRS_PROMPT = load(PROMPTS_DIR / "second_judge_pairs.txt")

#: The tasks, as the setting `tasks` and annotations/second_judge.csv's column task name them.
FACTS, PAIRS = "facts", "partial pairs"
TASK_SETTING = {"facts": (FACTS,), "partial_pairs": (PAIRS,), "both": (FACTS, PAIRS)}
#: The labels of each task, in the order the report lists them (the facts task's: the three kinds of decision of
#: annotations/second_opinion_candidates.csv, common/common_helpers/second_opinion.py, DECISIONS, with "left out"
#: standing for every "left out (<section>, rule <n>)").
LEFT_OUT = "left out"
LABELS = {FACTS: (ADDED, LEFT_OUT, IN_OTHER_WORDS), PAIRS: (SAME, NOT_SAME)}
#: The cache file of each task's answers (outputs/intermediate_results/second_judge/cache/<stage>.json).
STAGES = {FACTS: "facts", PAIRS: "partial_pairs"}

#: What "the same fact" means, quoted from 070_evaluate/metrics/pairs.md (its words as read without links; a test
#: keeps each quote in that file), for the partial pairs task's prompt. An occurrence there is an extracted triple.
PAIR_DEFINITIONS = (
    "A pair counts its occurrence as correct, for precision, and its ground truth triple as found, for recall. When "
    "the two don't state the same fact, or the fact they state is false, the occurrence is counted as correct and "
    "the ground truth triple as found, though neither should be.",
    "Subject instances or object instances that share words often refer to different things: \"MODIS Terra\" and "
    "\"MODIS\" are different instruments, and \"MODIS Snow Cover\" and \"MODIS Snow Cover Daily\" are different "
    "datasets.",
    "By contrast, \"MODIS Snow Cover\" is inside \"MODIS Snow Cover 5-Min L2 Swath\" as whole words: the same "
    "dataset, named more fully.",
    "A record describes a dataset made from both MODIS instruments, the one on Terra and the one on Aqua.",
    "E0's \"MODIS\" is less specific than \"Terra MODIS\", since it could name either instrument, but it names an "
    "instrument that did acquire the data, so the pair states the same fact, named differently.",
)

INPUTS = {
    "records":             "020_clean/records.jsonl",
    "splits":              "030_split/splits.json",
    "ground_truth_schema": "./annotations/ground_truth_schema.txt",
    "ground_truth":        "./annotations/ground_truth/batch_*.csv",
    "guidelines":          "./annotations/guidelines.md",
    "candidates":          "./annotations/second_opinion_candidates.csv",
    "partial_pairs":       "./annotations/partial_pairs_to_review.csv",
    "partial_reviews":     "./annotations/partial_pair_reviews.csv",
}
MAY_BE_EMPTY = ("candidates", "partial_pairs", "partial_reviews")

SETTINGS = {
    "tasks":              "both",  # which decisions to judge: facts, partial_pairs or both
    "ground_truth_at":    "",    # facts task: show the ground truth as it was at this Git commit; empty: as it is now
    "workers":            4,     # model calls made at the same time
    "service":            llm.SERVICE,  # the service that reaches the model: asksage or litellm
    "model":              SECOND_JUDGE_MODEL,  # the judge (py helpers/models.py lists them)
    "thinking":           "medium",  # how much a model that thinks may think: low, medium, high, or model_default
    "repeat":             1,     # which repeat of the same recipe: 2, 3, ... are asked again, with answers of their own
    "confirm_paid_calls": True,  # stop and ask before the first model call; false for unattended runs
}
SPECS = {"tasks": Spec(str, choices=tuple(TASK_SETTING)), "ground_truth_at": Spec(str)}

#: annotations/second_judge.csv: one row per judged item and model.
PATH = ANNOTATIONS_DIR / "second_judge.csv"
COLUMNS = ["task", "id", "title", "candidate_triple", "source_text", "ground_truth_triple", "extracted_triple", "model",
           "label", "rule", "reason"]
DETAILS_NAME = "second_judge_details.json"
#: The begin and end lines around a record's text in both prompts.
END_LINE = "----- END THE RECORD'S TEXT -----"

annotate = load_moves("050_annotate")                 # 050's moves: the records, the pool and the ground truth schema
records_stage = sys.modules["records"]                # 050's records.py: read_inputs


def triple_text(t: dict) -> str:
    """A classed triple in one line: subject (entity class) PREDICATE object (entity class)."""
    return f"{t['subject']} ({t['subject_class']}) {t['predicate']} {t['object']} ({t['object_class']})"


def label_of_decision(decision: str) -> tuple:
    """(label, rule) of a filled decision of annotations/second_opinion_candidates.csv: "left out (<section>, rule
    <n>)" is the label LEFT_OUT with the rule "<section>, rule <n>"; the other two have no rule."""
    d = decision.strip()
    if d.startswith(LEFT_OUT + " ("):
        return LEFT_OUT, d[len(LEFT_OUT) + 2:-1]
    return d, ""


# ------------------------------ choosing what to judge ------------------------------

def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True)


def ground_truth_at(commit: str, folder: Path, pool_rows: list, output: Path):
    """(the ground truth as it was at the Git commit, the commit's short hash): its files under the folder's path,
    copied from Git into output/ground_truth_at_<hash>/ and read as the ground truth is read."""
    found = _git("rev-parse", "--verify", "--short", f"{commit}^{{commit}}")
    if found.returncode:
        raise Stop(f"The setting ground_truth_at names {commit!r}, which isn't a commit of this repository, so the "
                   f"ground truth can't be read as it was then. Give a commit hash (`git log --oneline -- "
                   f"annotations/ground_truth` lists them), or leave it empty for the ground truth as it is now.")
    short = found.stdout.decode().strip()
    rel = Path(folder).resolve().relative_to(ROOT).as_posix()
    names = _git("ls-tree", "--name-only", short, f"{rel}/").stdout.decode("utf-8").split()
    target = output / f"ground_truth_at_{short}"
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    for name in names:
        if NUMBERED.fullmatch(Path(name).name):
            (target / Path(name).name).write_bytes(_git("show", f"{short}:{name}").stdout)
    return read_ground_truth(target, pool_rows), short


def _rows_text(rows: list) -> str:
    """The record's ground truth triples for the prompt, one per line, with their source text (never who drafted
    them)."""
    lines = [f"- {triple_text(r)} | source text: {r.get('source_text', '')}" for r in rows
             if r.get("subject") and r.get("predicate") and r.get("object")]
    return "\n".join(lines) or "(none)"


def facts_prompt(chosen, gt_rows: list, guidelines: str, row: dict) -> str:
    """The facts task's prompt for one candidate row: built from the record and the row's classed triple and source
    text only, so it is the same whatever the row's decision (the decision is never in it)."""
    record = chosen.records[row["id"]]
    return fill(FACTS_PROMPT, guidelines=guidelines.strip(), schema=chosen.schema_text, title=record.get("title") or "",
                text=llm.fence_safe(full_text(record), END_LINE), ground_truth=_rows_text(gt_rows),
                candidate=f"{triple_text(row)}\nSource text: {row['source_text']}")


def pairs_prompt(record: dict, row: dict) -> str:
    """The partial pairs task's prompt for one row of either file: the record and the two triples only (never a
    verdict), each as its verdict is filed (common/common_helpers/partial_reviews.py, pair_text), so a pair's prompt
    is the same whichever file holds its verdict."""
    return fill(PAIRS_PROMPT, definitions="\n".join(f"- {d}" for d in PAIR_DEFINITIONS),
                title=record.get("title") or "", text=llm.fence_safe(full_text(record), END_LINE),
                ground_truth_triple=pair_text(row, "ground_truth"), extracted_triple=pair_text(row, "translated"))


def _forbidden_makers(model: str, candidate_models: set) -> dict:
    """{maker: why} of the makers the judge may not come from: the extraction model's (llm.MODEL, the default of 060,
    whose extractions the partial pairs hold) and those of the models whose drafts the candidates come from."""
    out = {llm.maker(llm.MODEL): f"the extraction model {llm.MODEL}'s"}
    for m in sorted(candidate_models):
        out.setdefault(llm.maker(m), f"the second opinion's model {m}'s")
    out.pop(None, None)
    return out


def pick_items(inputs: dict, settings: dict, output: Path):
    """Every item to judge, with our label, its prompt and its cells for the CSV; and the notes shown before paying."""
    check_settings(settings, SPECS)
    tasks = TASK_SETTING[settings["tasks"].strip().lower()]
    chosen, pool_rows = records_stage.read_inputs(inputs)
    notes = [n for n in chosen.notes]
    try:
        candidates = read_candidates(inputs["candidates"]) if FACTS in tasks else []
    except ValueError as e:
        raise Stop(f"{e}. Fix it, then run this again.") from None
    model = str(settings["model"]).strip()
    forbidden = _forbidden_makers(model, {r["model"] for r in candidates})
    if llm.maker(model) is None:
        raise Stop(f"Which maker made {model!r} can't be told from its name (common/common_helpers/llm.py, MAKERS), "
                   f"so whether it is independent of the models whose decisions it judges can't be checked. Give a "
                   f"model whose name says its family, e.g. --model {SECOND_JUDGE_MODEL}.")
    if llm.maker(model) in forbidden:
        raise Stop(f"The judge {model} is made by {llm.maker(model)}, {forbidden[llm.maker(model)]} maker, so it "
                   f"isn't independent of the decisions it would judge (a model tends to favor output like its "
                   f"own). Give a model of another maker, e.g. --model {SECOND_JUDGE_MODEL}.")
    items, skipped = [], collections.defaultdict(list)

    if FACTS in tasks:
        guidelines = read_text(inputs["guidelines"])
        gt, at = chosen.ground_truth, ""
        if settings["ground_truth_at"].strip():
            gt, at = ground_truth_at(settings["ground_truth_at"].strip(), Path(inputs["ground_truth"]).parent,
                                     pool_rows, output)
            changed = _git("diff", "--quiet", at, "--", repo_path(inputs["guidelines"]),
                           repo_path(inputs["ground_truth_schema"]))
            if changed.returncode:
                notes.append(f"The guidelines or the ground truth schema changed since {at}, so the judge reads "
                             f"today's, not those the decisions were made with (`git diff {at} -- "
                             f"{repo_path(inputs['guidelines'])} {repo_path(inputs['ground_truth_schema'])}` shows "
                             f"how). Nothing to do unless a change decides a row.")
        by_record = collections.defaultdict(list)
        for r in gt.select(ANNOTATED).rows:               # every ground truth row of the record, whatever its state
            by_record[r["id"]].append(r)
        seen = set()
        for row in candidates:
            if not row["decision"]:
                skipped["facts: no decision yet"].append(row["id"])
                continue
            if candidate_key(row) in seen:                # one decision per fact, whichever model proposed it
                continue
            seen.add(candidate_key(row))
            if row["id"] not in chosen.records:
                skipped["facts: not a record of the catalog"].append(row["id"])
                continue
            ours, rule = label_of_decision(row["decision"])
            items.append({"task": FACTS, "id": row["id"], "title": row["title"], "ours": ours, "our_rule": rule,
                          "position": chosen.positions.get(row["id"]),
                          "cells": {"candidate_triple": triple_text(row), "source_text": row["source_text"]},
                          "prompt": facts_prompt(chosen, by_record.get(row["id"], []), guidelines, row)})
        models = {llm.model_name_key(r["model"]) for r in candidates}
        own = [r for rid in sorted({i["id"] for i in items}) for r in by_record.get(rid, [])
               if llm.model_name_key(r.get(DRAFTED_BY, "")) in models]
        if own and not at:
            notes.append(f"{len(own)} ground truth triple(s) of these records were drafted by the model the candidates "
                         f"come from ({named(sorted({r[DRAFTED_BY] for r in own}))}), so they were most likely added "
                         f"from these very candidates: the judge would see our decision in the ground truth. Give "
                         f"--ground_truth_at <the commit before the decisions changed the ground truth> "
                         f"(helpers/second_judge.md says which).")

    if PAIRS in tasks:
        to_review_path, reviews_path = Path(inputs["partial_pairs"]), Path(inputs["partial_reviews"])
        conflicts = review_conflicts(reviews_path) if reviews_path.is_file() else []
        if conflicts:
            raise Stop(f"{repo_path(reviews_path)} gives one pair two different verdicts, so our verdict on it isn't "
                       f"known: {'; '.join(conflicts)}. Keep the right row and delete the other (`py helpers/"
                       f"annotate.py`, view *Partial pairs*), then run this again.")
        to_review = read_csv_table(to_review_path)[1] if to_review_path.is_file() else []
        reviewed = read_csv_table(reviews_path)[1] if reviews_path.is_file() else []
        reviews = read_reviews(reviews_path)
        # every verdict, once per pair: the file to review's rows first (a verdict not yet moved, or the moved one),
        # then the moved verdicts whose pair is no longer in the file to review
        seen, mixed = {}, []
        for source, rows in ((to_review_path, to_review), (reviews_path, reviewed)):
            for row in rows:
                if not (row.get("record_id") or "").strip():
                    continue
                k = row_key(row)
                ours = verdict_of(row) if source == reviews_path else (verdict_of(row) or reviews.get(k, ""))
                where = f"{row['record_id']} ({repo_path(source)}, line {row['_line']})"
                if k in seen:
                    if ours and seen[k][0] and ours != seen[k][0]:
                        mixed.append(f"{seen[k][1]}: '{seen[k][0]}' and {where}: '{ours}'")
                    continue
                seen[k] = (ours, where, row)
        if mixed:
            raise Stop(f"{len(mixed)} pair(s) have different verdicts in {repo_path(to_review_path)} and "
                       f"{repo_path(reviews_path)}, so our verdict on them isn't known: {'; '.join(mixed)}. Make them "
                       f"agree (`py helpers/annotate.py`, view *Partial pairs*), then run this again.")
        for ours, where, row in seen.values():
            if ours not in (SAME, NOT_SAME):
                why = "no verdict yet" if not ours else f"a verdict that is neither {SAME!r} nor {NOT_SAME!r}"
                skipped[f"partial pairs: {why}"].append(where)
                continue
            if row["record_id"] not in chosen.records:
                skipped["partial pairs: not a record of the catalog"].append(row["record_id"])
                continue
            record = chosen.records[row["record_id"]]
            items.append({"task": PAIRS, "id": row["record_id"], "title": record.get("title") or "", "ours": ours,
                          "our_rule": "", "position": chosen.positions.get(row["record_id"]),
                          "cells": {"ground_truth_triple": pair_text(row, "ground_truth"),
                                    "extracted_triple": pair_text(row, "translated")},
                          "prompt": pairs_prompt(record, row)})

    for why, ids in skipped.items():
        notes.append(f"{len(ids)} row(s) not judged, {why}: {named(ids)}. A row is judged only once our label is "
                     f"filled, so that the judge's label can't shape ours: fill it, then run this again.")
    if settings["repeat"] > 1 and str(settings["service"]).strip().lower() == "litellm" and not llm.answer_cache_bypassed():
        notes.append(f"Repeat {settings['repeat']} may get repeat 1's answers: {llm.ANSWER_CACHE_SWITCH}=1 isn't set "
                     f"in .env, so LiteLLM may answer a repeated request from its own cache. Set it (`py "
                     f"helpers/check_answer_cache.py` tells whether the proxy caches), then run this again.")
    counts = collections.Counter(i["task"] for i in items)
    notes.append(f"This run asks {model} to judge " + " and ".join(f"{counts[t]} {t} row(s)" for t in tasks)
                 + f", without our labels, and writes its labels to {repo_path(PATH)}.")
    if not items:
        raise Stop("Nothing to judge: no row has our label yet. " + " ".join(notes))
    return items, tasks, notes, at if FACTS in tasks else ""


# ------------------------------ asking ------------------------------

def facts_shape(answer: dict) -> str | None:
    """What is wrong with a facts answer's shape, or None: a label of the three, a section heading, a rule number,
    a reason."""
    if str(answer.get("label", "")).strip().lower() not in LABELS[FACTS]:
        return f'"label" must be one of {", ".join(LABELS[FACTS])}, but is {answer.get("label")!r}'
    if not isinstance(answer.get("section"), str) or not answer["section"].strip():
        return '"section" must be the heading of the rule\'s section, a text'
    if isinstance(answer.get("rule"), bool) or not isinstance(answer.get("rule"), int):
        return f'"rule" must be the rule\'s number, a whole number, but is {answer.get("rule")!r}'
    if not isinstance(answer.get("reason"), str):
        return '"reason" must be a text'
    return None


def pairs_shape(answer: dict) -> str | None:
    """What is wrong with a partial pairs answer's shape, or None: a label of the two, a reason."""
    if str(answer.get("label", "")).strip().lower() not in LABELS[PAIRS]:
        return f'"label" must be one of {", ".join(LABELS[PAIRS])}, but is {answer.get("label")!r}'
    if not isinstance(answer.get("reason"), str):
        return '"reason" must be a text'
    return None


SHAPES = {FACTS: facts_shape, PAIRS: pairs_shape}


def ask(items: list, calls, settings: dict) -> dict:
    """Each item's answer ({index: answer}), from the cache when it holds one (each task's own file, keyed by the
    prompt and the model's settings: common/common_helpers/cache.py), else from one model call, `workers` at a time,
    asking once before the first. Failed items are left out of the answers, and listed in calls' failed."""
    caches = {t: Cache(calls.cache_dir, STAGES[t]) for t in LABELS}
    answers, todo = {}, {}
    for n, item in enumerate(items):
        k = cache_key(item["prompt"])
        stored = caches[item["task"]].get(k, SHAPES[item["task"]])
        if stored is not None:
            answers[n] = stored
        else:
            todo[n] = (k, item)
    calls.failed, calls.reused, calls.made_now = {}, len(answers), 0
    if not todo:
        return answers
    by_task = collections.Counter(item["task"] for _, item in todo.values())
    calls.paid.start(f"  the second judge will judge {len(todo)} row(s) ("
                     + ", ".join(f"{n} {t}" for t, n in by_task.items()) + f"), one model call each; {len(answers)} "
                     f"answered from the cache", to_pay=len(todo))
    before = calls.paid.made
    calls.paid.expect(len(todo))

    def one(n, k, item):
        reply = llm.call_llm_json(item["prompt"], check=SHAPES[item["task"]])
        calls.paid.made_call()
        return k, reply

    def handle(_, n, answer, error):
        item = todo[n][1]
        at = {"stage": STAGES[item["task"]], "record": item["id"]}
        if error is not None:
            calls.failed[n] = str(error)
            log.warning(f"judging failed for a {item['task']} row of {item['id']}: {error}")
            calls.paid.outcome(at, item["prompt"], error)
            return
        k, reply = answer
        answers[n] = reply
        caches[item["task"]].put(k, reply)
        calls.paid.outcome(at, item["prompt"])

    llm.run_parallel(one, {n: (n, k, item) for n, (k, item) in todo.items()}, settings["workers"], handle,
                     "Answers already received are kept in the cache; nothing else was written. Run this again to ask "
                     "the rest: the answers already received are reused, not paid for again.",
                     not_sent=lambda keys: calls.paid.not_sent(
                         [({"stage": STAGES[todo[n][1]["task"]], "record": todo[n][1]["id"]}, todo[n][1]["prompt"])
                          for n in keys]))
    calls.made_now = calls.paid.made - before
    return answers


def judged(items: list, answers: dict, rules: dict) -> list:
    """The items with the judge's label, rule and reason, and whether the rule is one the guidelines have."""
    out = []
    for n, item in enumerate(items):
        a = answers.get(n)
        if a is None:
            continue
        rule = ""
        if item["task"] == FACTS:
            rule = f"{a['section'].strip()}, rule {a['rule']}"
        out.append({**item, "label": str(a["label"]).strip().lower(), "rule": rule,
                    "reason": " ".join(str(a.get("reason", "")).split()),
                    "known_rule": item["task"] != FACTS or (a["section"].strip(), a["rule"]) in rules})
    return out


# ------------------------------ agreement ------------------------------

def agreement(pairs: list, labels: tuple) -> dict:
    """Agreement between two raters on the same items, pairs [(ours, the judge's)], over the labels:
    n; observed p_o = the share of items both label the same; expected p_e = Σ_k p_ours(k) × p_judge(k), each rater's
    own share of label k (Cohen 1960; Artstein & Poesio 2008, section 2.4); kappa κ = (p_o − p_e) / (1 − p_e), None
    when p_e = 1 (both raters gave every item one same label: nothing to correct for, κ undefined); per label: our
    count, the judge's, both, and the specific agreement 2 × both ÷ (ours + the judge's), None when neither used it
    (Cicchetti & Feinstein 1990); the confusion matrix {(ours, the judge's): count}; one_label: whether either rater
    used a single label (then p_o = p_e and κ = 0 whenever the other used two or more: degenerate). Fractions, exact."""
    n = len(pairs)
    matrix = collections.Counter(pairs)
    ours = collections.Counter(a for a, _ in pairs)
    theirs = collections.Counter(b for _, b in pairs)
    if not n:
        return {"n": 0, "observed": None, "expected": None, "kappa": None, "per_label": [], "matrix": matrix,
                "one_label": False}
    observed = Fraction(sum(matrix[(k, k)] for k in set(ours) | set(theirs)), n)
    expected = sum((Fraction(ours[k], n) * Fraction(theirs[k], n) for k in set(ours) | set(theirs)), Fraction(0))
    kappa = None if expected == 1 else (observed - expected) / (1 - expected)
    per = [{"label": k, "ours": ours[k], "judge": theirs[k], "both": matrix[(k, k)],
            "specific": Fraction(2 * matrix[(k, k)], ours[k] + theirs[k]) if ours[k] + theirs[k] else None}
           for k in list(labels) + sorted((set(ours) | set(theirs)) - set(labels))]
    return {"n": n, "observed": observed, "expected": expected, "kappa": kappa, "per_label": per, "matrix": matrix,
            "one_label": len(ours) == 1 or len(theirs) == 1}


def _f(v, digits: int = 3) -> str:
    return "–" if v is None else f"{float(v):.{digits}f}"


def _share(v) -> str:
    return "–" if v is None else f"{100 * float(v):.1f}%"


def agreement_lines(task: str, rows: list) -> list:
    """The report's section of one task: the numbers, the per-label table, the confusion matrix, the disagreements."""
    labels = LABELS[task]
    a = agreement([(r["ours"], r["label"]) for r in rows], labels)
    lines = [f"### {task.capitalize()}: agreement with our labels", ""]
    if not a["n"]:
        return lines + ["No row judged.", ""]
    agree = sum(a["matrix"][(k, k)] for k in labels)
    lines += [f"- **Raw agreement** *p*o = items both label the same ÷ items = {agree} ÷ {a['n']} = "
              f"**{_share(a['observed'])}**.",
              f"- **Agreement expected by chance** *p*e = Σ over the labels of our share × the judge's share = "
              f"{_f(a['expected'])}.",
              "- **Cohen's kappa** κ = (*p*o − *p*e) ÷ (1 − *p*e) = "
              + (f"**{_f(a['kappa'])}**" if a["kappa"] is not None else "**undefined** (*p*e = 1: both used one same "
                 "label for every row, so there is no chance agreement to correct for)") + "."]
    if a["one_label"] and a["kappa"] is not None:
        single = "we" if len({r["ours"] for r in rows}) == 1 else "the judge"
        lines.append(f"- **κ is degenerate here:** {single} used a single label, so *p*o = *p*e and κ = 0 whatever the "
                     f"other did. κ then says nothing; the raw agreement and the {a['n'] - agree} disagreement(s) "
                     f"below are what counts.")
    lines += ["", "| Label | Ours | The judge's | Both | Specific agreement 2 × both ÷ (ours + the judge's) |",
              "|---|---:|---:|---:|---:|"]
    lines += [f"| {p['label']} | {p['ours']} | {p['judge']} | {p['both']} | {_share(p['specific'])} |"
              for p in a["per_label"]]
    used = [p["label"] for p in a["per_label"]]
    lines += ["", "Rows: our label; columns: the judge's.", "", "| | " + " | ".join(used) + " |",
              "|---|" + "---:|" * len(used)]
    lines += [f"| {o} | " + " | ".join(str(a["matrix"][(o, j)]) for j in used) + " |" for o in used]
    if task == FACTS:
        both = [r for r in rows if r["ours"] == LEFT_OUT == r["label"]]
        same = sum(1 for r in both if r["rule"].lower() == r["our_rule"].lower())
        lines += ["", f"Of the {len(both)} row(s) both call left out, the judge names our rule in {same}."]
        unknown = [r for r in rows if not r["known_rule"]]
        if unknown:
            lines.append(f"The judge named {len(unknown)} rule(s) the guidelines don't have: "
                         f"{named(sorted({r['rule'] for r in unknown}), 10, '; ')}.")
    off = [r for r in rows if r["ours"] != r["label"]]
    lines += ["", f"#### {task.capitalize()}: the {len(off)} disagreement(s)", ""]
    for r in off:
        what = (r["cells"]["candidate_triple"] + f" — source text: {r['cells']['source_text']}" if task == FACTS else
                f"ground truth: {r['cells']['ground_truth_triple']}; extracted: {r['cells']['extracted_triple']}")
        lines.append(f"- **{cell(r['title'])}** (`{r['id']}`): {cell(what)}. Ours: {r['ours']}"
                     + (f" ({r['our_rule']})" if r["our_rule"] else "") + f"; the judge's: {r['label']}"
                     + (f" ({r['rule']})" if r["rule"] else "") + f". Its reason: {cell(r['reason'])}")
    return lines + [""]


# ------------------------------ writing ------------------------------

def write_table(rows: list, tasks: tuple, model: str, path: Path = PATH) -> int:
    """annotations/second_judge.csv: this run's rows for its tasks and model replace the earlier ones; every other
    row is kept. Ordered by task, then pool position."""
    old = read_csv_table(path)[1] if Path(path).is_file() else []
    kept = [{c: r.get(c, "") for c in COLUMNS} for r in old
            if not (r.get("task") in tasks and llm.model_name_key(r.get("model", "")) == llm.model_name_key(model))]
    new = [{"task": r["task"], "id": r["id"], "title": r["title"], **{c: "" for c in COLUMNS[3:7]}, **r["cells"],
            "model": model, "label": r["label"], "rule": r["rule"], "reason": r["reason"]} for r in rows]
    order = {t: i for i, t in enumerate(LABELS)}
    ordered = sorted(kept + new, key=lambda r: order.get(r["task"], len(order)))
    write_csv(path, COLUMNS, ordered)
    return len(ordered)


def main(inputs, settings, output):
    items, tasks, notes, at = pick_items(inputs, settings, output)        # code: the rows with our label; their prompts
    calls = llm.paid_calls(settings, output, notes=notes, command=COMMAND)  # code: asks once before paying
    answers = ask(items, calls, settings)                                 # LLM: one label per row, without ours
    rows = judged(items, answers, guideline_rules(inputs["guidelines"]))
    written = write_table(rows, tasks, llm.MODEL)                         # code: annotations/second_judge.csv
    warnings = list(notes)
    if calls.failed:
        warnings.append(f"{len(calls.failed)} row(s) couldn't be judged (the model call failed: "
                        f"{named(list(calls.failed.values()), 3, '; ')}), so they are left out of the agreement. Run "
                        f"`{COMMAND}` again: only those are asked again.")
    others = sorted(s for s in llm.SERVED if llm.maker(s) != llm.maker(llm.MODEL))
    if others:
        warnings.append(f"LiteLLM says the calls were answered by {named(others)}, not a model of "
                        f"{llm.maker(llm.MODEL)}'s, which {llm.MODEL} is: the judge may not be the one asked for. Ask "
                        f"NASA's LiteLLM administrators which model {llm.MODEL} reaches.")
    lines = [f"Judged by `{llm.MODEL}` ({llm.model_label()}), without seeing our labels: "
             + ", ".join(f"{sum(1 for r in rows if r['task'] == t)} {t} row(s)" for t in tasks)
             + (f"; the facts task's ground truth as it was at commit `{at}`" if at else "") + ". Each label is in "
             f"`{repo_path(PATH)}` ({written} row(s) in all). Raw agreement is given beside kappa because kappa "
             f"falls when one label is far more common than the others, however well the two agree (the prevalence "
             f"effect: Artstein & Poesio 2008, section 3.2): helpers/second_judge.md, *Agreement*.", ""]
    headline = {}
    for t in tasks:
        task_rows = [r for r in rows if r["task"] == t]
        lines += agreement_lines(t, task_rows)
        a = agreement([(r["ours"], r["label"]) for r in task_rows], LABELS[t])
        headline[f"{t}: rows judged"] = a["n"]
        headline[f"{t}: raw agreement"] = _share(a["observed"])
        headline[f"{t}: Cohen's kappa"] = _f(a["kappa"]) if a["kappa"] is not None else "undefined"
        headline[f"{t}: disagreements"] = sum(1 for r in task_rows if r["ours"] != r["label"])
        log.info(f"  {t}: {a['n']} row(s), raw agreement {_share(a['observed'])}, kappa "
                 f"{headline[f'{t}: Cohen' + chr(39) + 's kappa']}, {headline[f'{t}: disagreements']} disagreement(s)")
    lines += model_calls([(f"judge one row (stages {', '.join(STAGES[t] for t in tasks)})", calls.made_now,
                           calls.reused)], calls.paid.test_calls, llm.model_label())
    details = output / DETAILS_NAME
    made = {**llm.describe(), "settings": settings, "ground_truth_at": at or None}
    write_json(details, {"made": made, "rows": [{k: v for k, v in r.items() if k != "prompt"} for r in rows],
                         "failed": {items[n]["id"]: why for n, why in calls.failed.items()}})
    return Results(files=[details, PATH], headline=headline, details="\n".join(lines), warnings=warnings)


if __name__ == "__main__":
    run_step(STEP, INPUTS, SETTINGS, main, may_be_empty=MAY_BE_EMPTY, specs=SPECS, command=COMMAND, guide=GUIDE)
