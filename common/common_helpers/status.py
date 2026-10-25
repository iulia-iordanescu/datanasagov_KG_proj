"""
common/common_helpers/status.py -- where the project stands, and what to do next.

    from common.status import project_status, status_text, status_markdown
    st = project_status()          # {"steps": [...], "items": [...]}
    print(status_text(st))

Shown in three places, all from this one function: `py run_pipeline.py
--status` (in the terminal; it runs nothing and pays nothing), the section
*Needs attention* at the end of every pipeline report, and the annotation
tool's home page. What each item asks, and why, is explained in one place:
docs/upkeep.md, which each item names.

It only reads files: the steps' manifests (_manifest.json) and outputs, and
annotations/. No model is called. Some of what it reads holds model output
(050's drafted batches, 060's extracted triples, the rows 070 added to the
translation table), so an item is only as current as the run that wrote its
file: each item says which run that was, and a step whose inputs changed
since its run is listed as out of date.

Each item: {"area", "level", "text", "doc", "source"}
    area    Steps, Setup, Ground truth, Schema additions, Translation table,
            Partial pairs, Git
    level   "to do": something blocks a step or makes its numbers wrong;
            "worth a look": nothing stops, but a person should decide
    text    what is true, with ids and files, and the one thing to do
    doc     the section of docs/upkeep.md that explains it
    source  the run or file the item comes from

A step is out of date when an input it read has changed since its run: its
manifest records each input's fingerprint (sha256), compared here with the
files as they are now. Every input made by an earlier step counts. Of the
inputs a person makes (annotations/), only those that change the step's
result count (COUNTED_PERSON_INPUTS): the additions for 060, and for 070
everything it reads there. Step 050 is never out of date: each run drafts a
new drafted batch, and the drafted batches waiting are their own items. For 060, the
ground truth counts as finished records not extracted yet, not as a changed
file (annotating an unfinished record changes the file, not 060's work).
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import subprocess
from pathlib import Path

from common import audit
from common.component_class_mapping import CHECKED, MAPPING_PATH, crt_definitions, gtt_definitions, is_missing_target, \
    is_stale, is_stale_gtt, read_mapping, repeats
from common.ground_truth import (DRAFT_NUMBERED, DRAFT_PATTERN, GROUND_TRUTH_DIR, KIND_KEYS, NUMBERED, PATTERN,
                                 check_rows, ground_truth_schema_gaps, read_ground_truth, read_pool, with_coined)
from common.partial_reviews import REVIEWS_PATH, read_reviews, row_key
from common.report import named
from common.schema_io import addition_problem, additions_entries, read_ground_truth_schema
from common.step import ANNOTATIONS_DIR, MANIFEST_NAME, PIPELINE_STEPS, RESULTS_DIR, ROOT, input_files, repo_path
from common.triples_io import component_class_key

UPKEEP = "docs/upkeep.md"
GROUND_TRUTH_SCHEMA = ANNOTATIONS_DIR / "ground_truth_schema.txt"
ADDITIONS = ANNOTATIONS_DIR / "schema_additions.txt"
RECORDS = RESULTS_DIR / "020_clean" / "records.jsonl"
SPLITS = RESULTS_DIR / "030_split" / "splits.json"
DRAFTS_DIR = RESULTS_DIR / "050_annotate"
DETAILS = RESULTS_DIR / "060_extract" / "extracted_triples_details.json"
SCHEMA_USED = RESULTS_DIR / "060_extract" / "schema_used.json"
COMPARED = RESULTS_DIR / "070_evaluate" / "compared_triples.csv"

#: The inputs a person makes that change a step's result when they change (see the top of this file).
COUNTED_PERSON_INPUTS = {"060_extract": {"additions"},
                         "070_evaluate": {"ground_truth_schema", "ground_truth", "component_class_mapping",
                                          "partial_reviews"}}
#: The keys each service needs in .env (common/common_helpers/llm.py reads them).
SERVICE_KEYS = {"litellm": ("LITELLM_API_KEY",), "asksage": ("ASKSAGE_EMAIL", "ASKSAGE_API_KEY")}
TO_DO, LOOK = "to do", "worth a look"


def _doc(section: str) -> str:
    """A section of docs/upkeep.md, as a link target: "docs/upkeep.md#while-annotating"."""
    return f"{UPKEEP}#{section}"


def _item(area: str, level: str, text: str, section: str, source: str = "") -> dict:
    return {"area": area, "level": level, "text": text, "doc": _doc(section), "source": source}


def _manifest(step: str) -> dict | None:
    path = RESULTS_DIR / step / MANIFEST_NAME
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (ValueError, OSError):
        return None


def _when(manifest: dict) -> str:
    """When a run finished, as "2026-10-12 20:10"."""
    try:
        return dt.datetime.fromisoformat(manifest["finished"]).strftime("%Y-%m-%d %H:%M")
    except (KeyError, TypeError, ValueError):
        return "?"


# --------------------------------------------------------------------------
# what needs a person before the next drafted batch, or before 060 and 070 (also run_pipeline.py's gates)
# --------------------------------------------------------------------------

def unopened_drafts(drafts_dir: Path = DRAFTS_DIR, gt_dir: Path = GROUND_TRUTH_DIR) -> list:
    """The numbers of 050's drafted batches not opened yet in the annotation tool (no ground truth file of the same
    number), in order."""
    opened = {int(m.group(1)) for p in Path(gt_dir).glob(PATTERN) if (m := NUMBERED.fullmatch(p.name))}
    found = [int(m.group(1)) for p in Path(drafts_dir).glob(DRAFT_PATTERN) if (m := DRAFT_NUMBERED.fullmatch(p.name))] \
        if Path(drafts_dir).exists() else []
    return sorted(n for n in found if n not in opened)


def unfinished(gt) -> dict:
    """{ground truth file: [ids of its records not finished]}, files in order."""
    out = {}
    for rid, r in gt.records.items():
        if not r["finished"]:
            out.setdefault(r["file"], []).append(rid)
    return dict(sorted(out.items()))


def batch_waiting(drafts_dir: Path = DRAFTS_DIR, gt_dir: Path = GROUND_TRUTH_DIR, gt=None) -> str | None:
    """Why 050 shouldn't draft another drafted batch yet, or None: a drafted batch not opened yet in the annotation tool, or
    a ground truth file with a record not finished."""
    waiting = unopened_drafts(drafts_dir, gt_dir)
    if waiting:
        return f"drafted batch {waiting[0]} isn't opened yet in the annotation tool"
    left = unfinished(gt if gt is not None else read_ground_truth(gt_dir))
    if left:
        files = [repo_path(Path(gt_dir) / f) for f in left]
        ids = sorted(i for ids in left.values() for i in ids)
        return (f"{named(files)} {'has' if len(files) == 1 else 'have'} "
                f"{'a record' if len(ids) == 1 else f'{len(ids)} records'} not finished yet ({named(ids)})")
    return None


# --------------------------------------------------------------------------
# the steps
# --------------------------------------------------------------------------

def _changed_inputs(step: str, manifest: dict) -> list:
    """The names of the inputs that count (see the top of this file) whose files changed since the run."""
    changed = []
    for row in manifest.get("inputs", []):
        path = ROOT / row.get("path", "")
        made_by_a_step = path.resolve().is_relative_to(RESULTS_DIR.resolve())
        if not made_by_a_step and row.get("name") not in COUNTED_PERSON_INPUTS.get(step, set()):
            continue
        if audit.sha256(input_files(path)) != row.get("sha256"):
            changed.append(row.get("name"))
    return changed


def steps_status() -> list:
    """One entry per step: {"step", "state" ("ran", "out of date", "not run"), "run_id", "finished",
    "changed": [input names]}."""
    out = []
    for step in PIPELINE_STEPS:
        m = _manifest(step)
        if m is None:
            out.append({"step": step, "state": "not run", "run_id": None, "finished": None, "changed": []})
            continue
        changed = [] if step == "050_annotate" else _changed_inputs(step, m)
        out.append({"step": step, "state": "out of date" if changed else "ran", "run_id": m.get("run_id"),
                    "finished": _when(m), "changed": changed})
    return out


def _step_items(steps: list, gt) -> list:
    items, named_next = [], False
    finished = any(r["finished"] for r in gt.records.values())
    for s in steps:
        step, number = s["step"], s["step"][:3]
        if s["state"] == "not run":
            # Only the next step to run is named (the ones after it need its output first); a later step that
            # did run (its outputs copied from another computer, say) is still checked below.
            if named_next or (step in ("060_extract", "070_evaluate") and not finished)                     or (step == "050_annotate" and batch_waiting(gt=gt)):
                named_next = True                  # the ground truth items say what comes first
                continue
            named_next = True
            items.append(_item("Steps", TO_DO, f"Step {step} hasn't run on this computer yet: run it, "
                               f"`py {step}/run.py` (or `py run_pipeline.py --from {number}` for it and the steps "
                               f"after it).", "running-the-steps-again"))
            continue
        if s["state"] == "out of date":
            what = ", ".join(f"`{c}`" for c in s["changed"])
            if step == "030_split":
                do = (f"run it again (`py {step}/run.py`) to check that the split still holds: it keeps "
                      f"splits.json and warns if a new draw would differ")
            elif step == "070_evaluate" and all(c in COUNTED_PERSON_INPUTS[step] for c in s["changed"]):
                do = f"run it again (`py {step}/run.py`) to see the numbers with those changes"
            else:
                do = f"run it again, with the steps after it: `py run_pipeline.py --from {number}`"
            items.append(_item("Steps", TO_DO, f"Step {step} is out of date: its input(s) {what} changed since its "
                               f"run {s['run_id']} ({s['finished']}). To bring it up to date, {do}.",
                               "running-the-steps-again", s["run_id"] or ""))
    return items


def _setup_items(steps: list) -> list:
    """The key for the default service, once a step that calls the model is next."""
    try:
        from dotenv import dotenv_values
        env = {**dotenv_values(ROOT / ".env"), **os.environ}
    except ImportError:
        env = dict(os.environ)
    from common import llm
    missing = [k for k in SERVICE_KEYS.get(llm.SERVICE, ()) if not (env.get(k) or "").strip()]
    paying_ahead = any(s["state"] == "not run" for s in steps if s["step"][:3] in ("040", "050", "060", "070"))
    if missing and paying_ahead:
        return [_item("Setup", TO_DO, f"{' and '.join(missing)} {'is' if len(missing) == 1 else 'are'}n't in .env, "
                      f"so the steps that call the model (040, 050, 060, and 070, through {llm.SERVICE}, the default "
                      f"service) can't run on this computer: put {'it' if len(missing) == 1 else 'them'} in .env "
                      f"(docs/virtual_environment_setup.md, part 6).", "before-the-first-run")]
    return []


# --------------------------------------------------------------------------
# the ground truth, the ground truth schema, and the schema additions
# --------------------------------------------------------------------------

def _ground_truth_items(gt, schema: dict, records: dict | None, positions: dict) -> list:
    items = []
    shown = lambda rid: f"#{positions[rid]}" if rid in positions else rid      # as the annotation tool names a record
    for n in unopened_drafts():
        items.append(_item("Ground truth", TO_DO, f"Drafted batch {n} from step 050 isn't opened yet: open it in the "
                           f"annotation tool (`py helpers/annotate.py`, Ground truth, batch {n}) and correct it.",
                           "after-step-050-drafts-a-batch", repo_path(DRAFTS_DIR / f"drafted_triples_batch{n}.csv")))
    for file, ids in unfinished(gt).items():
        n = NUMBERED.fullmatch(file)
        where = f"Ground truth, batch {int(n.group(1))}" if n else "Ground truth"
        ids = sorted(ids, key=lambda rid: (rid not in positions, positions.get(rid, 0), rid))
        items.append(_item("Ground truth", TO_DO, f"{file} has {len(ids)} record(s) not finished (pool position): "
                           f"{named([shown(i) for i in ids], 5)}. "
                           f"Finish them in the annotation tool ({where}), ticking All facts extracted on each.",
                           "while-annotating", f"annotations/ground_truth/{file}"))
    for problem in gt.problems:
        items.append(_item("Ground truth", TO_DO, f"{problem}", "while-annotating", "annotations/ground_truth/"))
    if records:
        typos = check_rows(gt, records)
        if typos:
            items.append(_item("Ground truth", TO_DO, f"{len(typos)} ground truth triple(s) or describes triple(s) have an error "
                               f"to fix (each kind: 050_annotate/050_annotate.md, Checks on each row): "
                               f"{named([t['where'] for t in typos], 3)}. The annotation tool marks each with ✖.",
                               "while-annotating", "annotations/ground_truth/"))
    gaps = ground_truth_schema_gaps(schema, gt)
    if gaps["component_classes"]:
        coined = with_coined(schema, gt)["coined"]
        # every row of a finished record, its describes triple too (its entity class, as step 070 checks it)
        in_finished = {(kind, component_class_key(r[c])) for r in gt.rows if gt.records[r["id"]]["finished"]
                       for kind, cols in (("entity_classes", ("subject_class", "object_class")),
                                          ("predicates", ("predicate",))) for c in cols}
        stops = [n for kind in ("entity_classes", "predicates") for n in coined[kind]
                 if (kind, component_class_key(n)) in in_finished]
        names = [f"{g['component_class']} ({g['entry_type']}, coined in the ground truth)" for g in gaps["component_classes"]]
        items.append(_item("Ground truth", TO_DO, f"{len(names)} entity class(es) or predicate(s) the ground truth uses "
                           f"aren't in the ground truth schema: {named(names, 4, '; ')}. Add each with a one-line "
                           f"definition (annotation tool, the button under its ✖, or Help → Ground truth schema), or "
                           f"fix the typo." + (f" Step 070 stops while a finished record uses one ({len(stops)} do)."
                                               if stops else ""), "while-annotating",
                           repo_path(GROUND_TRUTH_SCHEMA)))
    return items


def _additions_items(parts: dict) -> list:
    items = []
    entries, unread = additions_entries(ADDITIONS)
    if unread:
        items.append(_item("Schema additions", TO_DO, f"{repo_path(ADDITIONS)} has {len(unread)} line(s) its layout "
                           f"can't read: fix them by hand (the file's comments at its top show the layout).",
                           "after-step-060", repo_path(ADDITIONS)))
    wrong = [p for e in entries if (p := addition_problem(e, parts))]
    if wrong:
        items.append(_item("Schema additions", TO_DO, f"{len(wrong)} entr(y/ies) of the schema additions to fix "
                           f"before step 060 runs again: {named(wrong, 2, '; ')}. Annotation tool, Schema additions.",
                           "after-step-060", repo_path(ADDITIONS)))
    if DETAILS.exists():
        details = json.loads(DETAILS.read_text(encoding="utf-8"))
        have = {(e["entry_type"], component_class_key(e.get("component_class"))) for e in entries}
        new = [n for n in (details.get("new_component_classes") or {}).get("component_classes", [])
               if (n["kind"], component_class_key(n["component_class"])) not in have]
        if new:
            m = _manifest("060_extract") or {}
            items.append(_item("Schema additions", LOOK, f"Step 060's model used {len(new)} component class(es) "
                               f"outside the schema, so step 060 removed those extracted triples: "
                               f"{named([n['component_class'] for n in new], 4)}. Add the ones that name a real type "
                               f"of thing or relationship (annotation tool, Schema additions).", "after-step-060",
                               m.get("run_id", "")))
    return items


# --------------------------------------------------------------------------
# the translation table and the partial pairs (after 060 and 070)
# --------------------------------------------------------------------------

def _translation_items(schema: dict, gt) -> list:
    if not SCHEMA_USED.exists() or not MAPPING_PATH.exists():
        return []
    crt = crt_definitions(json.loads(SCHEMA_USED.read_text(encoding="utf-8")))
    gtt_now = gtt_definitions(schema)                 # the file's own, as step 070 reads it: never a coined one
    table = read_mapping(MAPPING_PATH)
    current = [r for r in table if component_class_key(r["component_class_from_past_or_crt_schema"])
               in crt.get(r["kind"], {})]
    have = {(r["kind"], component_class_key(r["component_class_from_past_or_crt_schema"])) for r in table}
    without = [n for kind in KIND_KEYS for n in crt.get(kind, {}) if (kind, n) not in have]
    source = (_manifest("060_extract") or {}).get("run_id", "")
    items, where = [], "annotation tool, Translation table"
    if without:
        items.append(_item("Translation table", TO_DO, f"{len(without)} component class(es) of the current schema "
                           f"have no row in the translation table yet: step 070 adds them (one paid call per 100) and "
                           f"stops for you to check them.", "when-step-070-stops", source))
    unchecked = [r for r in current if r["checked"].lower() not in CHECKED]
    stale = [r for r in current if r["checked"].lower() in CHECKED and (is_stale(r, crt) or is_stale_gtt(r, gtt_now))]
    unknown = [r for r in current if r["checked"].lower() in CHECKED and is_missing_target(r, gtt_now)]
    repeated = repeats(table)
    for rows, what in ((unchecked, "still to check"),
                       (stale, "stale (a definition changed since the row was checked): check them again"),
                       (unknown, "with a missing target (translating to an entity class or predicate the ground "
                                 "truth schema doesn't have): choose the right one, or add it to the ground truth "
                                 "schema")):
        if rows:
            items.append(_item("Translation table", TO_DO, f"{len(rows)} row(s) of the translation table {what}: "
                               f"{named([r['component_class_from_past_or_crt_schema'] + ' (current schema)' for r in rows], 4)}. "
                               f"Step 070 stops on them until then ({where}).", "when-step-070-stops",
                               repo_path(MAPPING_PATH)))
    if repeated:
        items.append(_item("Translation table", TO_DO, f"{len(repeated)} component class(es) have more than one row "
                           f"in the translation table: keep one of each ({where}, Delete this row).",
                           "when-step-070-stops", repo_path(MAPPING_PATH)))
    return items


def _partial_items(parts_by_id: dict) -> list:
    if not COMPARED.exists():
        return []
    reviews = read_reviews(REVIEWS_PATH)
    with open(COMPARED, encoding="utf-8-sig", newline="") as fh:
        waiting = {row_key(r) for r in csv.DictReader(fh) if r.get("status") == "partial pair"
                   and parts_by_id.get(r.get("record_id")) == "tuning" and row_key(r) not in reviews}
    if not waiting:
        return []
    m = _manifest("070_evaluate") or {}
    return [_item("Partial pairs", LOOK, f"{len(waiting)} partial pair(s) of tuning records from step 070's run "
                  f"{m.get('run_id', '?')} aren't reviewed yet: mark each Same fact or Not the same fact (annotation "
                  f"tool, Partial pairs), then run step 070 again.", "after-step-070", m.get("run_id", ""))]


# --------------------------------------------------------------------------
# what isn't safe in Git yet
# --------------------------------------------------------------------------

def _git_items() -> list:
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", "annotations"], cwd=ROOT, capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    if r.returncode != 0:
        return []                                  # not a Git repository: nothing to say
    changed = [line[3:].strip().strip('"') for line in r.stdout.splitlines() if line.strip()]
    if not changed:
        return []
    return [_item("Git", TO_DO, f"{len(changed)} file(s) in annotations/ have changes not committed to Git: "
                  f"{named(changed, 4)}. Commit them, so the work is safe (and reaches the other computer).",
                  "after-every-session")]


# --------------------------------------------------------------------------
# all of it
# --------------------------------------------------------------------------

def project_status(records: dict | None = None) -> dict:
    """{"when", "steps": steps_status(), "items": [...]}: the items in the order the work comes (setup, steps,
    ground truth, schema additions, translation table, partial pairs, Git). records: 020's records by id, if
    already read (the annotation tool has them); read here otherwise."""
    from common.records_io import load_records
    gt = read_ground_truth()
    schema = read_ground_truth_schema(GROUND_TRUTH_SCHEMA) if GROUND_TRUTH_SCHEMA.exists() else \
        {"entity_classes": {}, "predicates": {}, "patterns": []}
    pool = read_pool(SPLITS) if SPLITS.exists() else []
    parts_by_id = {r["id"]: r.get("part") for r in pool}
    parts = {r["position"]: r.get("part") for r in pool}
    positions = {r["id"]: r["position"] for r in pool}
    if records is None:
        records = load_records(RECORDS) if RECORDS.exists() else None
    steps = steps_status()
    items = (_setup_items(steps) + _step_items(steps, gt) + _ground_truth_items(gt, schema, records, positions)
             + _additions_items(parts) + _translation_items(schema, gt) + _partial_items(parts_by_id) + _git_items())
    return {"when": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "steps": steps, "items": items}


def status_text(st: dict) -> str:
    """The status for the terminal."""
    lines = [f"Where the project stands ({st['when']}), and what to do next", "", "Steps on this computer:"]
    for s in st["steps"]:
        state = {"ran": f"ran {s['finished']} ({s['run_id']})",
                 "out of date": f"OUT OF DATE: ran {s['finished']} ({s['run_id']}); since then changed: "
                                f"{', '.join(s['changed'])}",
                 "not run": "not run on this computer"}[s["state"]]
        lines.append(f"  {s['step']:<19} {state}")
    for level, title in ((TO_DO, "To do"), (LOOK, "Worth a look")):
        mine = [i for i in st["items"] if i["level"] == level]
        lines += ["", f"{title}:"] + ([f"  {k}. [{i['area']}] {i['text']}\n     Why, and how: {i['doc']}"
                                       for k, i in enumerate(mine, 1)] or ["  nothing"])
    return "\n".join(lines)


def status_markdown(st: dict, docs_prefix: str = "") -> list:
    """The items as Markdown bullets, for a report (docs_prefix: the path from the report to the repository)."""
    out = []
    for level, title in ((TO_DO, "To do"), (LOOK, "Worth a look")):
        mine = [i for i in st["items"] if i["level"] == level]
        if mine:
            out += [f"**{title}**", ""] + [f"- **{i['area']}:** {i['text']} ([why, and how]({docs_prefix}{i['doc']}))"
                                         for i in mine] + [""]
    return out or ["Nothing to do."]
