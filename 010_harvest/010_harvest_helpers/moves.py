"""
moves.py -- the main moves of 010_harvest, as called by 010_harvest/run.py.

    stage 1  (here)  download_catalog  code: every page of the catalog into batch files, skipping pages on disk
    stage 2  (here)  check_complete    code: saved vs aimed for; repeated and missing ids; every file's request block
    -        (here)  results           writes the batch files (already on disk); the report

The API requests are in ckan_client.py, the batch files in batches.py.
Terms are as defined in docs/terminology.md.

A COMPLETE HARVEST IS KEPT. Once the batch files hold every record the
catalog reported when they were fetched, a rerun keeps them and asks the
catalog nothing: every later step (the pool, the split, the ground truth) is
built on them, and the live catalog may have changed since. Only
--new_harvest true replaces them, and then they are set aside in a folder
replaced_<date>/ beside the new ones, never deleted. A harvest that isn't
complete (a trial with max_records, an interrupted run) is continued as
before.

ORIGIN. 010 is where every item's origin starts. Each batch file wraps its
records with the request that returned them (see batches.py), so the records
themselves stay exactly as the API sent them. A batch kept from an earlier
run keeps the request block, and the run id, of the run that fetched it.
"""
from __future__ import annotations

import datetime as dt
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import batches
import ckan_client
from common.audit import current_run_id, log
from common.report import named, this_report
from common.step import ROOT, Results, check_settings

# Written by versions of this step that kept a separate lineage file. The
# request block in each batch file replaces it.
OLD_LINEAGE_FILE = "_lineage.jsonl"


@dataclass
class Harvest:
    folder: Path
    reported: int                 # catalog size according to the API
    target: int                   # how many records this run aims for
    page_size: int
    files: list = field(default_factory=list)    # this harvest's batch files, in order
    new: int = 0                                 # batch files downloaded this run
    reused: int = 0                              # batch files already on disk
    ran_dry: bool = False                        # API returned an empty page early
    replaced: int = 0                            # batch files on disk that didn't fit, fetched again
    removed: list = field(default_factory=list)  # batch files outside this run's range, deleted
    kept: bool = False                           # a complete harvest was saved, so this run kept it and asked nothing
    set_aside: str = ""                          # --new_harvest true: where the replaced harvest's batch files went


@dataclass
class Check:
    records: int
    unique_ids: int
    missing_ids: int
    duplicate_ids: int
    first_saved: dt.date
    last_saved: dt.date
    without_request: list         # batch files with no request block
    catalog_sizes: set            # the catalog's size as each page reported it


# --------------------------------------------------------------------------

def saved_harvest(folder: Path) -> Harvest | None:
    """The batch files on disk as a Harvest, if they are a COMPLETE harvest: they hold at least as many records as
    the catalog reported when the first page was fetched. None otherwise (no files, a trial, an interrupted run)."""
    files = batches.all_batches(folder)
    if not files:
        return None
    first = batches.load_batch(files[0])
    reported = first.get("catalog_count")
    saved = sum(len(batches.load_batch(p)["records"]) for p in files)
    if not reported or saved < reported:
        return None
    return Harvest(folder=folder, reported=reported, target=reported, page_size=len(first["records"]),
                   files=files, reused=len(files), kept=True)


def _set_aside(saved: Harvest) -> str:
    """Move a complete harvest's batch files into replaced_<date it was fetched>/ beside them; returns that folder's
    name. Never deletes: the replaced harvest may be what every later step was built on."""
    fetched = batches.load_batch(saved.files[0]).get("fetched_at", "")[:10] or dt.date.today().isoformat()
    target, n = saved.folder / f"replaced_{fetched}", 2
    while target.exists():
        target, n = saved.folder / f"replaced_{fetched}-{n}", n + 1
    target.mkdir()
    for p in saved.files:
        shutil.move(str(p), str(target / p.name))
    log.info(f"  --new_harvest true: moved the {len(saved.files)} batch files of the saved harvest to {target.name}/")
    return target.name


def download_catalog(settings: dict, output: Path) -> Harvest:
    check_settings(settings, {"page_size": 1, "max_records": 0, "pause_seconds": 0})
    page_size = settings["page_size"]
    max_records = settings["max_records"]
    pause = settings["pause_seconds"]

    for part in batches.leftover_parts(output):
        part.unlink()
    old_lineage = output / OLD_LINEAGE_FILE
    if old_lineage.exists():
        old_lineage.unlink()
        log.info(f"  removed {OLD_LINEAGE_FILE} (replaced by the request block in each batch file)")

    saved = saved_harvest(output)
    set_aside = ""
    if saved and not settings.get("new_harvest"):
        log.info(f"  a complete harvest is saved ({len(saved.files)} batch files, {saved.reported:,} records); "
                 f"kept, and the catalog not asked (--new_harvest true replaces it)")
        return saved
    if saved:
        set_aside = _set_aside(saved)

    session = ckan_client.make_session()
    first, first_request = ckan_client.fetch_page(session, 0, page_size)
    reported = first["count"]
    target = min(reported, max_records) if max_records > 0 else reported
    log.info(f"  catalog reports {reported} records; harvesting {target} in pages of {page_size}")

    harvest = Harvest(folder=output, reported=reported, target=target, page_size=page_size, set_aside=set_aside)

    for start in range(0, target, page_size):
        path = batches.batch_path(output, start)
        expected = min(page_size, target - start)

        if path.exists():
            batch = batches.load_batch(path)
            found = len(batch["records"])
            if not batch.get("request"):
                reason = "has no request block (old format)"
            elif not ckan_client.same_page(batch["request"], start, page_size):
                reason = "was requested differently (another page size or sort order)"
            elif found != expected:
                reason = f"holds {found} records, this run needs {expected}"
            else:
                harvest.files.append(path)
                harvest.reused += 1
                log.info(f"  {path.name} already on disk, kept")
                continue
            # Saved by a run with other settings (max_records, page_size), by
            # an older version of this step, or with another sort order.
            harvest.replaced += 1
            log.info(f"  {path.name} {reason}; downloading it again")

        if start == 0:
            page, request = first, first_request
        else:
            page, request = ckan_client.fetch_page(session, start, page_size)
        records = page["results"][:expected]
        if not records:
            harvest.ran_dry = True
            log.warning(f"empty page at start={start}, before the {target} records aimed for; the harvest "
                        f"stops here. Run `py 010_harvest/run.py` again later to fetch the remaining pages.")
            break

        header = {**request, "catalog_count": page["count"], "run_id": current_run_id()}
        batches.save_batch(path, header, records)
        harvest.files.append(path)
        harvest.new += 1
        log.info(f"  saved {path.name} ({len(records)} records, "
                 f"{min(start + page_size, target)}/{target})")
        time.sleep(pause)

    # Batch files beyond this run's range belong to an earlier, larger harvest.
    # 020_clean reads every batch file, so they would mix two harvests: remove them.
    mine = set(harvest.files)
    for p in batches.all_batches(output):
        if p not in mine:
            p.unlink()
            harvest.removed.append(p.name)
            log.info(f"  removed {p.name} (outside this run's range)")
    return harvest


def check_complete(harvest: Harvest) -> Check:
    seen, records, missing = set(), 0, 0
    dates, without_request, sizes = set(), [], set()
    for path in harvest.files:
        batch = batches.load_batch(path)
        for record in batch["records"]:
            records += 1
            rid = record.get("id")
            if rid is None:
                missing += 1
            else:
                seen.add(rid)
        if batch.get("catalog_count") is not None:
            sizes.add(batch["catalog_count"])
        # The harvest date is when each page was fetched, from its request block.
        if batch.get("request") and batch.get("fetched_at"):
            dates.add(dt.date.fromisoformat(batch["fetched_at"][:10]))
        else:
            without_request.append(path.name)
            dates.add(dt.date.fromtimestamp(path.stat().st_mtime))
    dates = dates or {dt.date.today()}

    return Check(records=records, unique_ids=len(seen), missing_ids=missing,
                 duplicate_ids=records - missing - len(seen),
                 first_saved=min(dates), last_saved=max(dates),
                 without_request=without_request, catalog_sizes=sizes)


def _shown(folder: Path) -> str:
    """The folder as a path from the repo root, for messages."""
    folder = folder.resolve()
    return folder.relative_to(ROOT).as_posix() if folder.is_relative_to(ROOT) else folder.as_posix()


def results(harvest: Harvest, check: Check) -> Results:
    warnings = []
    fresh = f"delete {_shown(harvest.folder)}/ and run `py 010_harvest/run.py` again"
    if check.records < harvest.target:
        warnings.append(f"Saved {check.records} records but expected {harvest.target}, so the harvest "
                        f"misses {harvest.target - check.records}. Either some pages weren't fetched "
                        f"(run `py 010_harvest/run.py` again to fetch them), or records were deleted from "
                        f"the catalog during the harvest: each deletion shifts the later pages back by "
                        f"one, so one record is missed. For a complete snapshot, {fresh}.")
    if harvest.ran_dry:
        warnings.append(f"The API returned an empty page before the reported count ({harvest.reported:,} "
                        f"records) was reached, so the harvest stopped there; the catalog may have shrunk "
                        f"during the harvest. Run `py 010_harvest/run.py` again later to fetch the "
                        f"remaining pages.")
    if len(check.catalog_sizes) > 1:
        warnings.append(f"The catalog's size changed while the pages were fetched (from "
                        f"{min(check.catalog_sizes):,} to {max(check.catalog_sizes):,} records, as the "
                        f"pages reported it). A record deleted meanwhile shifts the later pages back "
                        f"by one, so one record is missed, even when a record added meanwhile keeps "
                        f"the total right. For an exact snapshot, {fresh}.")
    if check.duplicate_ids:
        n = check.duplicate_ids
        warnings.append(f"{n} record{'s' if n != 1 else ''} appear{'' if n != 1 else 's'} twice. "
                        f"Pages are requested oldest record first, so a new or edited record "
                        f"shifts nothing; a repeat means a record reappeared in the middle of the "
                        f"order during the harvest (e.g. one restored after deletion), or that "
                        f"batch files kept from an earlier run overlap. `py 020_clean/run.py` keeps "
                        f"the first copy of each; for a clean snapshot, {fresh}.")
    if check.missing_ids:
        n = check.missing_ids
        warnings.append(f"{n} record{'s' if n != 1 else ''} {'have' if n != 1 else 'has'} no id, so no "
                        f"later step can tell {'them' if n != 1 else 'it'} apart from other records; "
                        f"`py 020_clean/run.py` drops {'them' if n != 1 else 'it'}. Nothing to do: "
                        f"{this_report('020_clean')}, section *Results*, subsection *What this run worked on*, "
                        f"lists each one (batch file, position, and title).")
    if harvest.reused and check.first_saved != check.last_saved:
        warnings.append(f"{harvest.reused} of {len(harvest.files)} batch files "
                        f"{'were' if harvest.reused != 1 else 'was'} kept from an "
                        f"earlier run, so this harvest mixes pages saved between "
                        f"{check.first_saved} and {check.last_saved}. Fine for development; for a "
                        f"single-day snapshot, {fresh}.")
    if check.without_request:
        shown = named(check.without_request)
        n = len(check.without_request)
        warnings.append(f"{n} batch file{'s have' if n != 1 else ' has'} no request block, so the "
                        f"request that returned their records is not recorded, and `py helpers/audit.py` "
                        f"can't trace them back to it: {shown}. Run `py 010_harvest/run.py` again to "
                        f"fetch them again.")

    if check.first_saved == check.last_saved:
        harvest_date = str(check.first_saved)
    else:
        harvest_date = f"{check.first_saved} to {check.last_saved}"

    kept_note = []
    if harvest.kept:
        kept_note = [f"**The saved harvest was kept.** Its batch files hold every record the catalog reported when "
                     f"they were fetched ({check.first_saved}), so this run asked the catalog nothing, and its "
                     f"settings page_size and max_records had no effect. Every later step (the pool, the split, "
                     f"the ground truth) is built on these files. To replace them on purpose: "
                     f"`py 010_harvest/run.py --new_harvest true`; they are then moved to "
                     f"`{_shown(harvest.folder)}/replaced_<date>/`, never deleted, and every later step must be "
                     f"run again (030 drops pool records no longer in the catalog). Details: "
                     f"010_harvest/010_harvest.md, section *How it works*.", ""]
    elif harvest.set_aside:
        kept_note = [f"**The saved harvest was replaced** (`--new_harvest true`): its batch files were moved to "
                     f"`{_shown(harvest.folder)}/{harvest.set_aside}/`, not deleted. Every later step must be run "
                     f"again on the new harvest: `py run_pipeline.py --from 020`.", ""]
    details = "\n".join(kept_note + [
        "### What this run worked on", "",
        "| | |", "|---|---|",
        f"| Records the catalog {'reported when the saved pages were fetched' if harvest.kept else 'reports'} | "
        f"{harvest.reported:,} |",
        f"| Records aimed for this run | {harvest.target:,} |",
        f"| Records saved | {check.records:,} |",
        f"| Distinct record ids | {check.unique_ids:,} |",
        f"| Batch files | {len(harvest.files)} ({harvest.new} downloaded, {harvest.reused} kept) |",
        f"| Batch files with their request block | "
        f"{len(harvest.files) - len(check.without_request)} of {len(harvest.files)} |",
        f"| Replaced from an earlier run | {harvest.replaced} (didn't fit this run's settings, "
        f"or had no request block) |",
        f"| Removed | {len(harvest.removed)} (outside this run's range) |",
        f"| Page size | {harvest.page_size} |",
        f"| Output folder | `{_shown(harvest.folder)}/` |",
    ])

    return Results(
        files=list(harvest.files),
        headline={"records harvested": check.records},
        details=details,
        warnings=warnings,
        harvest_date=harvest_date,
        harvest_partial=harvest.target < harvest.reported,
    )
