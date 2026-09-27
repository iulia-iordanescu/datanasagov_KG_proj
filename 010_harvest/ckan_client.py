"""
ckan_client.py -- talks to the data.nasa.gov catalog API.

data.nasa.gov runs CKAN, and CKAN's package_search action hands out records
in pages: rows = how many, start = where to begin. The first page also
reports how many records the catalog holds.

Every request is logged (URL, status, time taken) and described in a form
the lineage can store, so each saved record can be traced to the request
that returned it.
"""
from __future__ import annotations

import datetime as dt
import time

import requests
from requests.adapters import HTTPAdapter, Retry

from common.audit import log

URL = "https://data.nasa.gov/api/3/action/package_search"
TIMEOUT = (5, 60)          # seconds: (connect, read)
RETRIES = Retry(total=5, backoff_factor=1.5,
                status_forcelist=[429, 500, 502, 503, 504])


def make_session() -> requests.Session:
    """A session that retries busy or failing responses with growing pauses.
    Each retry is written to the log by the requests library."""
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=RETRIES))
    session.mount("http://", HTTPAdapter(max_retries=RETRIES))
    return session


def fetch_page(session: requests.Session, start: int, rows: int) -> tuple:
    """One page of the catalog. Returns (result, request), where result is
    {"count": <catalog size>, "results": [records]} and request describes
    the call for the lineage."""
    fetched_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.monotonic()
    resp = session.get(URL, params={"rows": rows, "start": start}, timeout=TIMEOUT)
    seconds = time.monotonic() - t0
    log.debug(f"GET {resp.url} -> {resp.status_code}, {len(resp.content):,} bytes in {seconds:.2f} s")
    resp.raise_for_status()
    body = resp.json()
    if not body.get("success", True):
        raise RuntimeError(f"CKAN reported failure for start={start}: {body.get('error')}")
    request = {"request": f"GET {resp.url}", "fetched_at": fetched_at,
               "http_status": resp.status_code}
    return body["result"], request
