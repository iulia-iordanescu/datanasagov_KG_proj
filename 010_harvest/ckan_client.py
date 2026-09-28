"""
ckan_client.py -- talks to the data.nasa.gov catalog API.

data.nasa.gov runs CKAN, and CKAN's package_search action hands out records
in pages: rows = how many, start = where to begin. The first page also
reports how many records the catalog holds.

Pages are requested in a fixed order, oldest record first (SORT). CKAN's
default order puts the most recently modified records first, so a record
added or edited during the ~23-minute harvest would jump ahead of the pages
already fetched: it would be missed, and every later page would shift by one
and repeat a record. In creation order, a new record lands at the end and an
edit moves nothing. Deleting a record still shifts the pages after it.

Every request is logged (URL, status, time taken) and described in a form
the batch file can store, so each saved record can be traced to the request
that returned it.
"""
from __future__ import annotations

import datetime as dt
import time
from urllib.parse import parse_qs, urlsplit

import requests
from requests.adapters import HTTPAdapter, Retry

from common.audit import log

URL = "https://data.nasa.gov/api/3/action/package_search"
# Seconds: (connect, read). A page of 1,000 records took 23-52 s to arrive on
# 2026-09-27; 120 s leaves room for a slower one without a retry, which would
# download the whole page again.
TIMEOUT = (5, 120)
RETRIES = Retry(total=5, backoff_factor=1.5,
                status_forcelist=[429, 500, 502, 503, 504])
# Oldest record first; the id breaks ties between records created in the same
# instant, so the order is the same on every request.
SORT = "metadata_created asc, id asc"


def page_params(start: int, rows: int) -> dict:
    """The query of the request for one page."""
    return {"rows": rows, "start": start, "sort": SORT}


def same_page(request_line: str | None, start: int, rows: int) -> bool:
    """Whether a saved batch file's request ("GET <url>") asked for exactly
    this page: same rows, start and sort order."""
    if not request_line:
        return False
    query = parse_qs(urlsplit(request_line.split(" ", 1)[-1]).query)
    wanted = {key: [str(value)] for key, value in page_params(start, rows).items()}
    return {key: query.get(key) for key in wanted} == wanted


def make_session() -> requests.Session:
    """A session that retries busy or failing responses: the first retry at
    once, then after 3, 6, 12 and 24 s (or the server's Retry-After). Each
    retry is written to the log by the underlying urllib3 library."""
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=RETRIES))
    session.mount("http://", HTTPAdapter(max_retries=RETRIES))
    return session


def fetch_page(session: requests.Session, start: int, rows: int) -> tuple:
    """One page of the catalog. Returns (result, request), where result is
    {"count": <catalog size>, "results": [records]} and request describes
    the call for the batch file's request block."""
    fetched_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    t0 = time.monotonic()
    resp = session.get(URL, params=page_params(start, rows), timeout=TIMEOUT)
    seconds = time.monotonic() - t0
    log.debug(f"GET {resp.url} -> {resp.status_code}, {len(resp.content):,} bytes in {seconds:.2f} s")
    resp.raise_for_status()
    body = resp.json()
    if not body.get("success", True):
        raise RuntimeError(f"CKAN reported failure for start={start}: {body.get('error')}")
    request = {"request": f"GET {resp.url}", "fetched_at": fetched_at,
               "http_status": resp.status_code}
    return body["result"], request
