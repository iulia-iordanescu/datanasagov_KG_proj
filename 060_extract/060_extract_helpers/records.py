"""
records.py -- stage 1: which records this run extracts from.

The setting `extract_from` says which:

    ground_truth   (default) the records of the ground truth a person has
                   finished (all facts extracted on every row), the only ones
                   070 can evaluate; a record still in progress is skipped
    all            every record with text: once the schema is final

or `ids` names exactly the records, as in 050 (common/common_helpers/records_io.read_ids).
Anything that makes the run differ from what was asked (a listed id not in
the catalog or without text, a record not yet finished, …) becomes a NOTE,
shown before the paid-call question and in the report.
"""
from __future__ import annotations


from dataclasses import dataclass, field
from pathlib import Path

from common.chunking import full_text, pieces
from common.ground_truth import DRAFTED_BY, read_ground_truth, read_pool
from common.llm import maker
from common.records_io import NOT_IN_CATALOG, WITHOUT_TEXT, WITHOUT_TEXT_TO_DO, has_text, load_records, read_ids
from common.report import named
from common.step import check_settings, input_files, repo_path
from common.stop import Stop

MODES = ("ground_truth", "all")


#: 060's own reason for skipping a record (the shared ones: common/common_helpers/records_io.py).
NOT_FINISHED = "not finished in the ground truth"

@dataclass
class Chosen:
    items: list = field(default_factory=list)      # {"id", "title", "maintainer", "text", "pieces"}
    records: dict = field(default_factory=dict)    # every record, {id: record}
    ground_truth: set = field(default_factory=set) # ids of every record in the ground truth
    how: str = ""                                  # the choice in words, for the report
    notes: list = field(default_factory=list)      # where the run differs from what was asked
    skipped: dict = field(default_factory=dict)    # {reason: [ids]}
    pool: dict = field(default_factory=dict)       # {id: (pool position, "tuning" | "held-out")} (030's splits.json)


def pick_records(inputs: dict, settings: dict) -> Chosen:
    check_settings(settings, {})
    if settings["extract_from"] not in MODES:
        raise Stop(f"extract_from must be one of {', '.join(MODES)} (got {settings['extract_from']!r}), so 060 "
                   f"can't choose records. Set --extract_from to {' or '.join(MODES)} (or name the records with "
                   f"--ids), then run `py 060_extract/run.py` again.")
    chosen = Chosen(records=load_records(inputs["records"]))
    chosen.pool = {r["id"]: (r["position"], r.get("part")) for r in read_pool(inputs["splits"])}
    gt_files = input_files(Path(inputs["ground_truth"]))
    ids = read_ids(settings["ids"])
    if not gt_files and not ids and settings["extract_from"] == "ground_truth":
        raise Stop(f"No ground truth files at {repo_path(inputs['ground_truth'])}, so 060 has no finished records to "
                   f"extract from (extract_from is ground_truth). Annotate records first (`py 050_annotate/run.py`, "
                   f"then `py helpers/annotate.py`), or set --extract_from all, or name the records with --ids, "
                   f"then run `py 060_extract/run.py` again.")
    # No ground truth files is fine for extract_from all and for ids: no record is then in the ground truth.
    gt = read_ground_truth(gt_files[0].parent if gt_files else Path(inputs["ground_truth"]).parent)
    chosen.ground_truth = {r["id"] for r in gt.rows}
    chosen.notes += [f"Ground truth, {p}" for p in gt.problems]
    skipped = {NOT_IN_CATALOG: [], WITHOUT_TEXT: [], NOT_FINISHED: []}

    if ids:
        chosen.how = f"the {len(ids)} id(s) given in the setting ids"
        if settings["extract_from"] != "ground_truth":
            chosen.notes.append(f"extract_from ({settings['extract_from']}) is ignored, because the setting ids "
                                f"names the records: this run extracts from the records listed in ids. To extract "
                                f"from {settings['extract_from']} records instead, leave ids empty.")
        wanted = ids
    elif settings["extract_from"] == "ground_truth":
        finished = [rid for rid, r in gt.records.items() if r["finished"]]
        skipped[NOT_FINISHED] = [rid for rid, r in gt.records.items() if not r["finished"]]
        chosen.how = f"the {len(finished)} finished record(s) of the ground truth"
        wanted = finished
    else:
        chosen.how = "every record with text"
        wanted = list(chosen.records)

    for rid in wanted:
        record = chosen.records.get(rid)
        if record is None:
            skipped[NOT_IN_CATALOG].append(rid)
        elif not has_text(record):
            skipped[WITHOUT_TEXT].append(rid)
        else:
            chosen.items.append({"id": rid, "title": record.get("title") or "", "maintainer": record.get("maintainer"),
                                 "text": full_text(record),
                                 "pieces": pieces(record, settings["max_chars"])})
    chosen.skipped = {k: v for k, v in skipped.items() if v}

    to_do = {      # what to do about records skipped for each reason (worded as in 050)
        NOT_IN_CATALOG: f"Check these ids in {'the setting ids' if ids else 'annotations/ground_truth/'} "
                              f"for typos: each must be a record id in {repo_path(inputs['records'])}.",
        WITHOUT_TEXT: WITHOUT_TEXT_TO_DO}
    for reason, rids in chosen.skipped.items():
        if reason == WITHOUT_TEXT and not ids and settings["extract_from"] == "all":
            continue                                             # expected: most catalogs have a few
        if reason == NOT_FINISHED:
            chosen.notes.append(f"{len(rids)} record(s) of the ground truth aren't finished yet (all facts "
                                f"extracted not ticked), so skipped: {named(rids)}. Step 070 evaluates only "
                                f"finished records. To include them, finish them in `py helpers/annotate.py` "
                                f"(tick All facts extracted), then run `py 060_extract/run.py` again.")
        else:
            who = "record(s) you listed" if ids else "ground truth record(s)"
            chosen.notes.append(f"{len(rids)} {who} {'are' if len(rids) > 1 else 'is'} {reason}, "
                                f"so skipped: {named(rids)}. {to_do[reason]}")
    if not chosen.items:
        raise Stop("Nothing to extract: none of the records chosen can be extracted from, so 060 can't write "
                   "extracted triples. " + " ".join(chosen.notes) + " Change the settings as these reasons say, "
                   "then run `py 060_extract/run.py` again.")
    chosen.notes += same_model_notes(gt, {i["id"] for i in chosen.items}, settings["model"])
    return chosen


def same_model_notes(gt, ids: set, model: str) -> list:
    """A note when the ground truth of the records chosen was drafted (050, column drafted_by) by this run's model,
    or by another model of the same maker: facts that model misses tend to be missing from both the ground truth
    and the extraction, so recall would look better than it is (070_evaluate/metrics/recall.md)."""
    by_drafter = {}
    for r in gt.rows:
        if r["id"] in ids and r.get(DRAFTED_BY):
            by_drafter.setdefault(r[DRAFTED_BY], set()).add(r["id"])
    notes, mine = [], maker(model)
    for drafter, rids in sorted(by_drafter.items()):
        if drafter == model:
            how = f"the same model as this run's ({model})"
        elif mine and maker(drafter) == mine:
            how = f"a model from the same maker ({mine}) as this run's {model}"
        else:
            continue
        notes.append(f"The ground truth of {len(rids)} of the records chosen was drafted (step 050) by {drafter}, "
                     f"{how}: facts that model misses tend to be missing from both the ground truth and the "
                     f"extraction, so recall would look better than it is. To avoid it, run `py 060_extract/run.py` "
                     f"with --model naming a model from another maker (`py helpers/models.py` lists them).")
    return notes
