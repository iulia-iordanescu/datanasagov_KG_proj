"""
common/common_helpers/llm_costs.py -- what a run's model calls cost, and how long they took.

A part of common/common_helpers/llm.py: each reply's token counts kept apart by the price they are billed at
(count_priced: batch or single request, the prompt-length tier, the date), the cost of a run at the makers' list
prices (run_cost, with llm.PRICES), a batch job's processing time from the times its maker reports (job_processing),
and what a run's record keeps of all three (spent). Import these names from common.llm, never from this file.

The cost is computed from the service's token counts and the listed prices, not read from the maker's invoice: a
discount, a credit, a tax or a price change after the prices were read doesn't show in it.
"""

import datetime as dt

from common import llm
from common.llm import (
    DIRECT_SERVICES, PRICE_FIELDS, PRICE_PAGES, PRICES, SERVICES, TOKENS_BY_PRICE, _last, _requests_lock,
    model_name_key)


#: The counts kept for each (kind, tier, day) of TOKENS_BY_PRICE, in this order in the run's record.
COUNTS = ("answers", "input_tokens", "cache_read_tokens", "cache_write_tokens", "cache_write_1h_tokens",
          "output_tokens", "reasoning_tokens")


#: Which price field each count is billed at (llm.PRICE_FIELDS); reasoning tokens are part of the output tokens.
BILLED_AS = {"input_tokens": "input", "cache_read_tokens": "cache_read", "cache_write_tokens": "cache_write",
             "cache_write_1h_tokens": "cache_write_1h", "output_tokens": "output"}


def price_entry(model: str | None = None, service: str | None = None) -> dict | None:
    """The model's entry of llm.PRICES (names compared as llm.model_name_key compares them), or None: not listed, or
    the service isn't the maker's own API the prices are for."""
    model, service = model or llm.MODEL, service or llm.SERVICE
    entry = {model_name_key(k): v for k, v in PRICES.items()}.get(model_name_key(model))
    return entry if entry and entry["service"] == service else None


def tier_of(prompt_tokens: int, model: str | None = None, service: str | None = None) -> str:
    """"long" when a request's prompt (all its input tokens, the cached ones included) is longer than the model's
    long_above (llm.PRICES), else "base"."""
    entry = price_entry(model, service)
    above = entry["long_above"] if entry else None
    return "long" if above is not None and (prompt_tokens or 0) > above else "base"


def _today() -> str:
    return dt.datetime.now().astimezone().date().isoformat()


def _anthropic_writes(usage: dict, write: int, batch: bool) -> tuple:
    """(writes at the 5-minute lifetime, writes at the 1-hour lifetime) of an Anthropic reply: its usage's
    cache_creation split (ephemeral_5m_input_tokens, ephemeral_1h_input_tokens; the Messages API's Usage object), or,
    when the reply has none, the lifetime the request was sent with: the 1-hour cache in a batch request
    (llm_batch.ANTHROPIC_CACHE_TTL), the 5-minute one in a single request."""
    split = ((usage.get("maker_usage") or {}).get("cache_creation")
             if isinstance(usage.get("maker_usage"), dict) else None)
    if isinstance(split, dict) and (split.get("ephemeral_5m_input_tokens") is not None
                                    or split.get("ephemeral_1h_input_tokens") is not None):
        return int(split.get("ephemeral_5m_input_tokens") or 0), int(split.get("ephemeral_1h_input_tokens") or 0)
    from common.llm_batch import ANTHROPIC_CACHE_TTL
    return (0, write) if batch and ANTHROPIC_CACHE_TTL == "1h" else (write, 0)


def count_priced(usage: dict, read: int, write: int, output: int, reasoning: int) -> None:
    """Add one reply's token counts to llm.TOKENS_BY_PRICE, under (kind, tier, day): "batch" when the reply is an
    answer of a batch job (the request's record names the job: llm._last.reply["batch_job"]), else "single"; the tier
    from the prompt's length (tier_of); the day the request was made: the batch job's creation (batch_created), or
    today for a single request. read, write, output, reasoning: as _count_tokens read them from usage."""
    reply = getattr(_last, "reply", None) or {}
    batch = bool(reply.get("batch_job"))
    day = (str(reply.get("batch_created") or "")[:10] or _today()) if batch else _today()
    prompt = usage.get("prompt_tokens") or 0
    short, long_ = (_anthropic_writes(usage, write, batch) if llm.SERVICE == "anthropic" else (write, 0))
    key = ("batch" if batch else "single", tier_of(prompt), day)
    with _requests_lock:
        counts = TOKENS_BY_PRICE.setdefault(key, dict.fromkeys(COUNTS, 0))
        counts["answers"] += 1
        counts["input_tokens"] += prompt - read - write
        counts["cache_read_tokens"] += read
        counts["cache_write_tokens"] += short
        counts["cache_write_1h_tokens"] += long_
        counts["output_tokens"] += output
        counts["reasoning_tokens"] += reasoning


def by_price_rows(buckets: dict | None = None) -> list:
    """TOKENS_BY_PRICE as the run's record keeps it: [{"kind", "tier", "day", counts...}], sorted."""
    buckets = TOKENS_BY_PRICE if buckets is None else buckets
    return [{"kind": k, "tier": t, "day": d, **dict(c)} for (k, t, d), c in sorted(buckets.items())]


def period_on(entry: dict, day: str) -> dict | None:
    """The price period of a PRICES entry that covers the date day (YYYY-MM-DD), or None."""
    for period in entry["periods"]:
        if (period["from"] is None or day >= period["from"]) and (period["through"] is None or day <= period["through"]):
            return period
    return None


def run_cost(rows: list, model: str | None = None, service: str | None = None) -> dict:
    """The cost of a run's token counts (rows: by_price_rows) at the model's list prices (llm.PRICES): {"usd": the
    total in US dollars, or None when it can't be computed; "unknown": why not, or None; "parts": [each row with
    "price" (the prices used, US dollars per million tokens) and "usd"]; "prices_from": the price page}. Batch rows at
    the batch prices, single rows at the standard ones, each at its tier's and its day's prices. Never estimated: a
    service other than the maker's own API, a model not listed, a day no price period covers, or tokens of a kind
    with no listed price make the whole cost unknown, saying which."""
    model, service = model or llm.MODEL, service or llm.SERVICE
    if service not in DIRECT_SERVICES:
        return {"usd": None, "parts": [], "prices_from": None,
                "unknown": (f"the calls went through {SERVICES.get(service, service)}, which bills its own account; "
                            f"the prices kept here (PRICES in common/common_helpers/llm.py) are the list prices of the "
                            f"makers' own APIs (the services anthropic, openai and google)")}
    entry = price_entry(model, service)
    if entry is None:
        return {"usd": None, "parts": [], "prices_from": PRICE_PAGES[service],
                "unknown": (f"PRICES in common/common_helpers/llm.py lists no price for the model {model} through "
                            f"{SERVICES[service]}: add its prices from {PRICE_PAGES[service]}, with the page's rows "
                            f"quoted beside them")}
    parts, total, unknown = [], 0.0, []
    for row in rows:
        period = period_on(entry, row["day"])
        if period is None:
            unknown.append(f"no price of {model} listed in PRICES covers {row['day']}, the day its {row['kind']} "
                           f"requests were made")
            parts.append({**row, "price": None, "usd": None})
            continue
        name = ("batch" if row["kind"] == "batch" else "standard") + ("_long" if row["tier"] == "long" else "")
        price = period[name]
        usd = 0.0
        for count, field in BILLED_AS.items():
            n = row.get(count) or 0
            if not n:
                continue
            if price[field] is None:
                unknown.append(f"{n:,} {count.replace('_', ' ')} of {row['kind']} requests, and PRICES lists no "
                               f"{field.replace('_', ' ')} price for {model}")
                usd = None
                break
            usd += n * price[field] / 1_000_000
        parts.append({**row, "price": dict(price), "usd": usd})
        if usd is not None:
            total += usd
    return {"usd": None if unknown else total, "parts": parts, "prices_from": PRICE_PAGES[service],
            "unknown": "; ".join(unknown) or None}


def money(usd) -> str:
    """US dollars in words: "$1.23", "$0.0042" below a cent; "unknown" for None."""
    if usd is None:
        return "unknown"
    return f"${usd:,.2f}" if usd >= 0.01 or usd == 0 else f"${usd:.4f}"


# ------------------------------ time ----------------------------------------------

#: The maker-reported times a batch job's record keeps (llm_batch: _poll), by service, under the maker's own field
#: names: Anthropic's MessageBatch created_at and ended_at (RFC 3339 times); OpenAI's Batch created_at,
#: in_progress_at, finalizing_at, completed_at, failed_at, expired_at, cancelled_at (Unix seconds); google-genai's
#: BatchJob create_time, start_time, end_time and update_time (datetimes; google/genai/types.py says of end_time
#: "This field is for Gemini Enterprise Agent Platform only", so through the Gemini API a job's end is read from
#: update_time, "The time when the BatchJob was last updated", once the job has ended). Each kept as an ISO 8601
#: time with its offset.
MAKER_TIME_FIELDS = {
    "anthropic": ("created_at", "ended_at"),
    "openai": ("created_at", "in_progress_at", "finalizing_at", "completed_at", "failed_at", "expired_at",
               "cancelled_at"),
    "google": ("create_time", "start_time", "end_time", "update_time"),
}


#: The fields a job's processing time is measured between, by service: (its creation, the fields that may hold its
#: end, the first one present used).
PROCESSING_FIELDS = {
    "anthropic": ("created_at", ("ended_at",)),
    "openai": ("created_at", ("completed_at", "failed_at", "expired_at", "cancelled_at")),
    "google": ("create_time", ("end_time", "update_time")),
}


def iso_time(value) -> str | None:
    """A maker's time as an ISO 8601 text with its offset: Unix seconds (OpenAI) as UTC, a datetime as it is (UTC
    when it carries no offset), an ISO text as it is (a final Z as +00:00); None for none."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat()
    if isinstance(value, dt.datetime):
        return (value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)).isoformat()
    text = str(value).strip()
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)).isoformat()


def maker_times(service: str, job) -> dict:
    """The times the maker reports for a job (MAKER_TIME_FIELDS), from its reply (a dict, or an SDK object), each as
    iso_time gives it; the fields it doesn't report left out."""
    out = {}
    for field in MAKER_TIME_FIELDS.get(service, ()):
        value = job.get(field) if isinstance(job, dict) else getattr(job, field, None)
        value = iso_time(value)
        if value:
            out[field] = value
    return out


def job_processing(service: str, times: dict | None) -> dict | None:
    """A job's processing time at the maker: {"seconds", "from": the creation field, "to": the end field used}, its
    end minus its creation (PROCESSING_FIELDS); None when the times don't hold both."""
    if not times:
        return None
    start, ends = PROCESSING_FIELDS.get(service, (None, ()))
    end = next((f for f in ends if times.get(f)), None)
    if not (start and times.get(start) and end):
        return None
    try:
        seconds = (dt.datetime.fromisoformat(times[end]) - dt.datetime.fromisoformat(times[start])).total_seconds()
    except (TypeError, ValueError):
        return None
    return {"seconds": round(seconds, 1), "from": start, "to": end}


def wall_time() -> dict | None:
    """The run's wall time so far: {"started": the run's start, "until": now, "seconds"}, measured from the start
    common/common_helpers/step.py gives the run (audit.run_started); None outside a run."""
    from common import audit
    started = audit.run_started()
    if not started:
        return None
    iso, clock = started
    return {"started": iso, "until": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "seconds": round(llm.time.monotonic() - clock, 1)}


def spent() -> dict:
    """What a run's record keeps of what its model calls used (each step's "made", under "spent"): its tokens (in
    total, as REQUESTS counts them, and by price, by_price_rows), its cost (run_cost) and its wall time (wall_time,
    from the run's start to when the record is written). A batch job's maker-reported times and processing time are
    kept with the job (llm.describe: batch_jobs)."""
    rows = by_price_rows()
    return {"tokens": {k: v for k, v in llm.REQUESTS.items() if k != "sent"}, "tokens_by_price": rows,
            "cost": run_cost(rows), "wall_time": wall_time()}


def cost_lines() -> list:
    """The report's lines on the run's cost (common/common_helpers/report.py, model_calls): a table of the tokens by
    price and what each part cost, then the total, said to be computed from the service's token counts and the
    listed prices, not the maker's invoice."""
    rows = by_price_rows()
    cost = run_cost(rows)
    head = ("Cost: computed from the service's token counts above and the maker's list prices (`PRICES` in "
            "`common/common_helpers/llm.py`" + (f", from {cost['prices_from']}, read 2026-11-18" if cost["prices_from"]
                                                 else "") + "), not read from the maker's invoice.")
    if cost["usd"] is None and not cost["parts"]:
        return [f"Cost: unknown: {cost['unknown']}.", ""]
    if not cost["parts"]:
        return [head + " Total: $0.00: no request of this run reported token counts (every answer came from the "
                       "cache, or no model call was made).", ""]
    lines = ["| Tokens by price | Answers | Sent, not from the cache | Read from the cache | Written to the cache "
             "| Received | Price (US dollars per million tokens) | Cost |", "|---|---:|---:|---:|---:|---:|---|---:|"]
    for p in cost["parts"]:
        what = (("batch requests (batch price)" if p["kind"] == "batch" else "single requests (standard price)")
                + (f", prompts over {price_entry()['long_above']:,} tokens" if p["tier"] == "long" else "")
                + f", {p['day']}")
        writes = f"{p['cache_write_tokens'] + p['cache_write_1h_tokens']:,}" + (
            f" ({p['cache_write_1h_tokens']:,} to the 1-hour cache)" if p["cache_write_1h_tokens"] else "")
        lines.append(f"| {what} | {p['answers']:,} | {p['input_tokens']:,} | {p['cache_read_tokens']:,} | "
                     f"{writes} | {p['output_tokens']:,} | {_price_words(p['price'])} | {money(p['usd'])} |")
    total = (f" Total: {money(cost['usd'])}." if cost["usd"] is not None else f" Total: unknown: {cost['unknown']}.")
    return lines + ["", head + total + " Each answer is counted at the price of its kind: an answer of a batch job "
                    "at the batch price, every other request (the one-line test call, a second ask, an answer cut "
                    "off at a batch API's lower limit and asked again) at the standard price; received tokens include "
                    "the thinking. A batch job collected by this run counts in this run, whichever run sent it.", ""]


def _price_words(price: dict | None) -> str:
    if not price:
        return "none listed"
    names = {"input": "input", "cache_read": "cache read", "cache_write": "cache write",
             "cache_write_1h": "1-hour cache write", "output": "output"}
    return ", ".join(f"{names[f]} {('$' + format(price[f], 'g')) if price[f] is not None else 'not listed'}"
                     for f in PRICE_FIELDS if price[f] is not None or f in ("input", "cache_read", "output"))


def time_lines() -> list:
    """The report's line on time: each batch job's processing time at the maker (job_processing), and where the run's
    wall time is."""
    jobs = [j for j in llm.BATCH_JOBS if j.get("id")]
    if not jobs:
        return ["Time: the run's wall time is its Duration, under Run.", ""]
    from common.report import _duration
    each = []
    for j in jobs:
        p = job_processing(j.get("service") or llm.SERVICE, j.get("maker_times"))
        each.append(f"`{j['id']}` " + (f"{_duration(p['seconds'])} ({p['from']} {j['maker_times'][p['from']]} to "
                                       f"{p['to']} {j['maker_times'][p['to']]})" if p else
                                       "not known (the maker reported no end time while this run read it)"))
    return [f"Time: each batch job's processing time at the maker, its end minus its creation as the maker reported "
            f"them: {'; '.join(each)}. The run's wall time is its Duration, under Run.", ""]
