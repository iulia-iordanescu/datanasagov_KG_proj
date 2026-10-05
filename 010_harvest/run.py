"""
010 · Harvest

Downloads the whole data.nasa.gov catalog, page by page, from its public
CKAN API. Each page is saved as it arrives, so an interrupted run loses at
most one page, and a rerun keeps the pages already on disk. Terms:
docs/terminology.md.

Reads:   nothing (the data.nasa.gov API)
Writes:  batch_*.json, one per page: the raw records, with the request that
         returned them
Details: 010_harvest/010_harvest.md
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common.step import load_moves, run_step

INPUTS = {}

SETTINGS = {
    "page_size":     1000,  # records per request (CKAN's usual maximum)
    "max_records":   0,     # 0 = whole catalog; e.g. 2000 for a quick trial run
    "pause_seconds": 0.5,   # wait between requests, to be polite to the server
}

harvest = load_moves("010_harvest")


def main(inputs, settings, output):
    pages = harvest.download_catalog(settings, output)   # code: every page, skipping pages on disk
    check = harvest.check_complete(pages)                # code: saved = reported? any repeated ids?
    # writes the batch files; the report
    return harvest.results(pages, check)


if __name__ == "__main__":
    run_step("010_harvest", INPUTS, SETTINGS, main)
