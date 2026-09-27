"""
moves.py -- the main moves of 010_harvest, as called by 010_harvest.py.

    download_catalog   fetch every page of the catalog into batch files,
                       skipping pages already on disk
    check_complete     compare what was saved with what the API reported, and
                       check every saved record has a lineage row
    results            package files, headline numbers, report text, warnings

LINEAGE. Each saved record gets one row in _lineage.jsonl linking it to the
API request that returned it:

    output   {"file": "batch_01000.json", "position": 17, "key": <record id>}
    sources  [{"kind": "api", "request": "GET https://...&start=1000",
               "position": 17, "fetched_at": ..., "http_status": 200}]

Rows are written just before their batch file, so a batch on disk always has
its lineage. A batch kept from an earlier run keeps that run's rows.
"""
from __future__ import annotations

import datetime as dt
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import batches
import ckan_client
from common.audit import LINEAGE_NAME, lineage, log
from common.step import ROOT, Results


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


@dataclass
class Check:
    records: int
    unique_ids: int
    missing_ids: int
    duplicate_ids: int
    first_saved: dt.date
    last_saved: dt.date
    lineage_rows: int             # records with a lineage row
    kept_without_lineage: list    # kept batch files whose lineage is unknown


# --------------------------------------------------------------------------

def download_catalog(settings: dict, output: Path) -> Harvest:
    page_size = settings["page_size"]
    max_records = settings["max_records"]
    pause = settings["pause_seconds"]

    for part in batches.leftover_parts(output):
        part.unlink()

    session = ckan_client.make_session()
    first, first_request = ckan_client.fetch_page(session, 0, page_size)
    reported = first["count"]
    target = min(reported, max_records) if max_records > 0 else reported
    log.info(f"  catalog reports {reported} records; harvesting {target} in pages of {page_size}")

    harvest = Harvest(folder=output, reported=reported, target=target, page_size=page_size)

    for start in range(0, target, page_size):
        path = batches.batch_path(output, start)
        expected = min(page_size, target - start)

        if path.exists():
            found = len(batches.load_batch(path))
            if found == expected:
                harvest.files.append(path)
                harvest.reused += 1
                lineage().keep(path.name)
                log.info(f"  {path.name} already on disk, kept")
                continue
            # Saved by a run with other settings (max_records, page_size): replace it.
            harvest.replaced += 1
            log.info(f"  {path.name} holds {found} records, this run needs {expected}; "
                     f"downloading it again")

        if start == 0:
            page, request = first, first_request
        else:
            page, request = ckan_client.fetch_page(session, start, page_size)
        records = page["results"][:expected]
        if not records:
            harvest.ran_dry = True
            log.warning(f"empty page at start={start}; stopping")
            break

        for position, record in enumerate(records):
            lineage().add(path.name, position, record.get("id"),
                          [{"kind": "api", **request, "position": position}])
        lineage().flush()
        batches.save_batch(path, records)
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
    seen, records, missing, per_file = set(), 0, 0, {}
    for path in harvest.files:
        batch = batches.load_batch(path)
        per_file[path.name] = len(batch)
        for record in batch:
            records += 1
            rid = record.get("id")
            if rid is None:
                missing += 1
            else:
                seen.add(rid)

    rows = lineage().finish([p.name for p in harvest.files])
    for name, n in per_file.items():
        if rows.get(name, 0) != n:
            log.debug(f"lineage: {name} has {rows.get(name, 0)} rows for {n} records")

    # The harvest date comes from the lineage (when each page was fetched);
    # the file's modification date stands in for pages with no lineage.
    dates = set()
    fetched = _fetch_dates(harvest.folder)
    for path in harvest.files:
        dates.add(fetched.get(path.name) or dt.date.fromtimestamp(path.stat().st_mtime))
    dates = dates or {dt.date.today()}

    return Check(records=records, unique_ids=len(seen), missing_ids=missing,
                 duplicate_ids=records - missing - len(seen),
                 first_saved=min(dates), last_saved=max(dates),
                 lineage_rows=sum(min(rows.get(name, 0), n) for name, n in per_file.items()),
                 kept_without_lineage=list(lineage().kept_without_lineage))


def _shown(folder: Path) -> str:
    """The folder as a path from the repo root, for messages."""
    folder = folder.resolve()
    return folder.relative_to(ROOT).as_posix() if folder.is_relative_to(ROOT) else folder.as_posix()


def _fetch_dates(folder: Path) -> dict:
    """{batch file: date its page was fetched}, read back from _lineage.jsonl."""
    dates = {}
    path = folder / LINEAGE_NAME
    if path.exists():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                name = row["output"]["file"]
                if name not in dates and row["sources"]:
                    dates[name] = dt.date.fromisoformat(row["sources"][0]["fetched_at"][:10])
    return dates


def results(harvest: Harvest, check: Check) -> Results:
    warnings = []
    if check.records < harvest.target:
        warnings.append(f"Saved {check.records} records but expected {harvest.target}. "
                        "Rerun to fetch the missing pages.")
    if harvest.ran_dry:
        warnings.append("The API returned an empty page before the reported count was reached; "
                        "the catalog may have shrunk during the harvest.")
    if check.duplicate_ids:
        n = check.duplicate_ids
        warnings.append(f"{n} record{'s' if n != 1 else ''} appear{'' if n != 1 else 's'} twice, "
                        f"and probably as many were skipped: records added to the catalog "
                        f"mid-harvest shift the pages. 020_clean must drop the repeats; only a fresh "
                        f"harvest (delete the folder, rerun) fetches the skipped ones.")
    if check.missing_ids:
        warnings.append(f"{check.missing_ids} records have no id.")
    if harvest.reused and check.first_saved != check.last_saved:
        warnings.append(f"{harvest.reused} of {len(harvest.files)} batch files were kept from an "
                        f"earlier run, so this harvest mixes pages saved between "
                        f"{check.first_saved} and {check.last_saved}. For a single-day snapshot, "
                        f"delete {_shown(harvest.folder)}/ and rerun.")
    if check.lineage_rows < check.records:
        missing_rows = check.records - check.lineage_rows
        detail = (f" Kept from an earlier run without lineage: "
                  f"{', '.join(check.kept_without_lineage[:5])}"
                  f"{' …' if len(check.kept_without_lineage) > 5 else ''}."
                  if check.kept_without_lineage else "")
        warnings.append(f"{missing_rows:,} saved records have no lineage row, so the request that "
                        f"returned them is not recorded.{detail} Delete those batch files and "
                        f"rerun to fetch them again with lineage.")

    if check.first_saved == check.last_saved:
        harvest_date = str(check.first_saved)
    else:
        harvest_date = f"{check.first_saved} to {check.last_saved}"

    details = "\n".join([
        "| | |", "|---|---|",
        f"| Records the catalog reports | {harvest.reported:,} |",
        f"| Records aimed for this run | {harvest.target:,} |",
        f"| Records saved | {check.records:,} |",
        f"| Distinct record ids | {check.unique_ids:,} |",
        f"| Records with lineage | {check.lineage_rows:,} |",
        f"| Batch files | {len(harvest.files)} ({harvest.new} downloaded, {harvest.reused} kept) |",
        f"| Replaced from an earlier run | {harvest.replaced} (didn't fit this run's settings) |",
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
    )
