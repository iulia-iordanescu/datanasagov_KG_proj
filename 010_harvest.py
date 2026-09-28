"""
010 · Harvest

Downloads the whole data.nasa.gov catalog, page by page, from its public
CKAN API. Each page is saved as it arrives, so an interrupted run loses at
most one page, and a rerun keeps the pages already on disk.

Reads:   nothing (the data.nasa.gov API)
Writes:  batch_*.json, one file per page: the raw records, with the request
         that returned them
Details: instructions/010_harvest.md
"""
from common.step import run_step, helpers

INPUTS = {}

SETTINGS = {
    "page_size":     1000,  # records per request (CKAN's usual maximum)
    "max_records":   0,     # 0 = whole catalog; e.g. 2000 for a quick trial run
    "pause_seconds": 0.5,   # wait between requests, to be polite to the server
}

catalog = helpers("010_harvest")


def main(inputs, settings, output):
    harvest = catalog.download_catalog(settings, output)   # every page, skipping pages on disk
    check = catalog.check_complete(harvest)                # saved = reported? any repeated ids?
    return catalog.results(harvest, check)                 # files, headline, report, warnings


if __name__ == "__main__":
    run_step("010_harvest", INPUTS, SETTINGS, main)
