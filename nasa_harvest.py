# nasa_harvest.py desc: download the entire data.nasa.gov catalog to disk
#
# breakdown:
#   - the API hands out records in pages: rows=how many, start=where to begin.
#   - the loop: start=0, 1000, 2000... until we've collected everything.
#   - each page is saved to data\batch_00000.json etc. as soon as it arrives,
#     so a crash or Ctrl+C loses at most one page.
#   - resume support: already-saved batches are skipped on rerun.

import json
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter, Retry

URL = "https://data.nasa.gov/api/3/action/package_search"
PAGE_SIZE = 1000                # records per request (CKAN's usual max)
OUT_DIR = Path("data")          # data\ subfolder, created automatically
OUT_DIR.mkdir(exist_ok=True)

session = requests.Session()
retries = Retry(total=5, backoff_factor=1.5,
                status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))


def fetch_page(start: int) -> dict:
    resp = session.get(URL, params={"rows": PAGE_SIZE, "start": start},
                       timeout=(5, 60))
    resp.raise_for_status()
    return resp.json()["result"]


def main() -> None:
    # first call learns the total so we know when we're done
    first = fetch_page(0)
    total = first["count"]
    print(f"Catalog reports {total} datasets. Harvesting in pages of {PAGE_SIZE}...\n")

    start = 0
    while start < total:
        batch_file = OUT_DIR / f"batch_{start:05d}.json"

        if batch_file.exists():                      # resume: skip what we have
            print(f"  {batch_file.name} already on disk, skipping")
            start += PAGE_SIZE
            continue

        result = first if start == 0 else fetch_page(start)
        records = result["results"]
        if not records:                              # safety: API ran dry early
            print("  API returned an empty page — stopping.")
            break

        batch_file.write_text(json.dumps(records), encoding="utf-8")
        print(f"  saved {batch_file.name}  ({len(records)} records, "
              f"{min(start + PAGE_SIZE, total)}/{total} done)")

        start += PAGE_SIZE
        time.sleep(0.5)         

    n_files = len(list(OUT_DIR.glob("batch_*.json")))
    print(f"\nHarvest complete: {n_files} batch files in {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
