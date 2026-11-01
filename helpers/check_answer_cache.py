"""
helpers/check_answer_cache.py -- does NASA's LiteLLM answer repeated requests from its own cache?

    py helpers/check_answer_cache.py                    claude-opus-5.5 (the default model)
    py helpers/check_answer_cache.py --model <name>     another model

Why: on 2026-10-31, py helpers/check_effort.py sent each of its three settings
the same request 3 times through NASA's LiteLLM, and each setting's 3 answers
used exactly the same number of completion tokens (717, 717, 717; 814, 814,
814; 802, 802, 802), from a model with no temperature sent and with adaptive
thinking. That suggests the proxy answers a repeated identical request from a
cache of its own. If it does, the runs of a recipe's repeats (the setting
`repeat`) would be copies of one run, not independent answers of the model.

LiteLLM's proxy has an answer cache that is off until its configuration turns
it on (https://docs.litellm.ai/docs/proxy/caching: "Caching is enabled by
adding the `cache` key to the `config.yaml`"; a repeated request then gets the
cached answer, which "carries an `x-litellm-cache-key` response header"). A
request can ask the proxy not to use it, in its body
(https://docs.litellm.ai/docs/proxy/caching_controls): {"cache": {"no-cache":
true}}, "Force a fresh response, bypassing the cache", and {"cache":
{"no-store": true}}, "Will not cache the response". Those docs don't say what a
proxy with caching off does with these controls.

The check sends one small request whose answer can vary ("Write one sentence
about the Moon.", no temperature for Claude, with a tag naming this check's
time, so no earlier request was the same) twice as it is, then twice more with
{"cache": {"no-cache": true, "no-store": true}}: 4 tiny paid calls, asked
about before paying. For each it prints the HTTP status, whether the reply
carries x-litellm-cache-key, the completion tokens, the answer, and every
cache-related usage field and response header. The decision rule is fixed
before the calls and printed first (RULE). It also prints whether the proxy
accepted the cache control (no 4xx), and what to do: with "LiteLLM answers from
its cache" and the control accepted, put LITELLM_BYPASS_ANSWER_CACHE=1 in .env,
and every LiteLLM request of the pipeline then carries the control
(common/common_helpers/llm.py, ANSWER_CACHE_CONTROL).

Needs the NASA network and your key in .env (docs/running_on_nasa_laptop.md).
Not a pipeline step: it writes nothing. Put what it prints in docs/findings.md.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common import llm

#: The response header LiteLLM's proxy puts on an answer it serves from its cache.
CACHE_HEADER = "x-litellm-cache-key"

#: The question: a one-sentence answer, whose words can vary from call to call when no temperature is sent.
QUESTION = "Write one sentence about the Moon."

#: The cache control the second pair of calls carries (the one the pipeline sends when the bypass is on).
CONTROL = llm.ANSWER_CACHE_CONTROL

#: The 4 calls: a name for the printout, and what is added to the request.
CALLS = (("plain call 1", {}), ("plain call 2", {}), ("no-cache call 1", CONTROL), ("no-cache call 2", CONTROL))

CACHE_VERDICT = "LiteLLM answers from its cache"
NO_CACHE_VERDICT = "no answer cache seen"
NOT_SHOWN = "not shown"

RULE = (f"Decision rule (fixed before the calls): \"{CACHE_VERDICT}\" if the second plain call carries "
        f"{CACHE_HEADER} or returns a byte-identical answer with identical usage, while the no-cache calls differ "
        f"from each other or carry no {CACHE_HEADER}; \"{NO_CACHE_VERDICT}\" if no call carries {CACHE_HEADER} and "
        f"the two plain answers differ; \"{NOT_SHOWN}\" otherwise, with the reason. Separately: the proxy accepted "
        f"the cache control if neither no-cache call was refused (HTTP 4xx).")


def tag() -> str:
    """This check's time, put in the question so the proxy can't hold an answer to it from an earlier run."""
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def question(at: str) -> str:
    return f"{QUESTION} (Request tag {at}: ignore it.)"


def cache_fields(usage: dict, headers: dict) -> dict:
    """Every cache-related usage field (at any depth: e.g. prompt_tokens_details.cached_tokens) and response header."""
    found = {}

    def walk(value, path):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, f"{path}.{k}" if path else str(k))
        elif "cache" in path.lower():
            found[f"usage {path}"] = value
    walk(usage or {}, "")
    for k, v in (headers or {}).items():
        if "cache" in str(k).lower():
            found[f"header {k}"] = v
    return found


def ask(model: str, text: str, extra: dict) -> dict:
    """One request through LiteLLM: {"status", "key" (the CACHE_HEADER value, or None), "text" (the answer, or the
    service's error text), "usage", "cache_fields"}."""
    url, headers = llm._litellm("/v1/chat/completions")
    payload = {"model": model, "messages": [{"role": "user", "content": text}],
               "max_tokens": llm.MAX_ANSWER_TOKENS, **json.loads(json.dumps(extra))}
    if llm.temperature_sent(model, "litellm"):
        payload["temperature"] = llm.TEMPERATURE                # as the pipeline sends it; never to Claude
    resp = llm._post(url, headers=headers, json=payload, timeout=(5, llm.READ_TIMEOUT))
    got = {str(k).lower(): v for k, v in dict(getattr(resp, "headers", None) or {}).items()}
    if resp.status_code >= 400:
        return {"status": resp.status_code, "key": got.get(CACHE_HEADER), "text": resp.text, "usage": {},
                "cache_fields": cache_fields({}, got)}
    body = resp.json()
    usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
    answer = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
    return {"status": resp.status_code, "key": got.get(CACHE_HEADER), "text": answer, "usage": usage,
            "cache_fields": cache_fields(usage, got)}


def same(a: dict, b: dict) -> bool:
    """Two answered calls with a byte-identical answer and identical usage."""
    return a["status"] == b["status"] == 200 and a["text"] == b["text"] and a["usage"] == b["usage"]


def accepted(calls: list) -> tuple:
    """(whether the proxy accepted the cache control, in words): accepted if neither no-cache call was refused."""
    refused = [c["status"] for c in calls[2:] if 400 <= c["status"] < 500]
    if refused:
        return False, (f"refused (HTTP {refused[0]}): the proxy doesn't take the cache control. Its error text: "
                       f"{next(c['text'] for c in calls[2:] if 400 <= c['status'] < 500)}")
    failed = [c["status"] for c in calls[2:] if c["status"] != 200]
    if failed:
        return None, f"not known: a no-cache call failed with HTTP {failed[0]}, which isn't a refusal; run the check again"
    return True, "accepted (both no-cache calls answered with HTTP 200)"


def verdict(calls: list) -> tuple:
    """(CACHE_VERDICT, NO_CACHE_VERDICT or NOT_SHOWN, the reason) for the 4 calls, in CALLS' order: each {"status",
    "key", "text", "usage"}."""
    p1, p2, n1, n2 = calls
    if p1["status"] != 200 or p2["status"] != 200:
        bad = next(c["status"] for c in (p1, p2) if c["status"] != 200)
        return NOT_SHOWN, f"a plain call failed (HTTP {bad}), so the two plain answers can't be compared"
    plain_hit = p2["key"] is not None or same(p1, p2)
    no_cache_ok = n1["status"] == 200 and n2["status"] == 200
    no_cache_fresh = no_cache_ok and (not same(n1, n2) or (n1["key"] is None and n2["key"] is None))
    if plain_hit and no_cache_fresh:
        why = (f"the second plain call carries {CACHE_HEADER}" if p2["key"] is not None
               else "the second plain call returned a byte-identical answer with identical usage")
        fresh = ("differ from each other" if not same(n1, n2) else f"carry no {CACHE_HEADER}")
        return CACHE_VERDICT, f"{why}, while the no-cache calls {fresh}"
    keys = [c for c in calls if c["key"] is not None]
    if not keys and p1["text"] != p2["text"]:
        return NO_CACHE_VERDICT, f"no call carries {CACHE_HEADER}, and the two plain answers differ"
    if plain_hit and not no_cache_ok:
        return NOT_SHOWN, ("the plain calls look cached, but a no-cache call wasn't answered, so there is nothing "
                           "to compare them with")
    if plain_hit:
        return NOT_SHOWN, (f"the plain calls look cached, but so do the no-cache calls (identical, and carrying "
                           f"{CACHE_HEADER}): the proxy ignored the cache control")
    if keys:
        return NOT_SHOWN, (f"{', '.join(CALLS[calls.index(c)][0] for c in keys)} carries {CACHE_HEADER}, but the "
                           f"second plain call doesn't and isn't identical to the first")
    return NOT_SHOWN, ("no call carries the header, but the two plain answers have the same words with different "
                       "usage, which neither a cached answer nor a fresh one explains")


def advice(found: str, taken: bool | None) -> str:
    """What to do with the bypass switch (LITELLM_BYPASS_ANSWER_CACHE in .env), for a verdict and acceptance."""
    if taken is False:
        return ("Leave LITELLM_BYPASS_ANSWER_CACHE unset: the proxy refuses the cache control, so every request "
                "carrying it would fail. Ask NASA's LiteLLM administrators to turn the answer cache off for this key.")
    if found == CACHE_VERDICT and taken:
        return ("Put the line LITELLM_BYPASS_ANSWER_CACHE=1 in .env: every LiteLLM request of the pipeline then asks "
                "for a fresh answer and not to keep it, and each run's record says \"LiteLLM answer cache: "
                "bypassed\". Runs of repeat 2 and later made before then may be copies of repeat 1: run them again.")
    if found == NO_CACHE_VERDICT:
        return "Nothing to change: the repeats' answers are the model's own."
    return "Run the check again; if it still shows nothing, ask NASA's LiteLLM administrators whether caching is on."


def show(name: str, call: dict) -> None:
    print(f"  {name}: HTTP {call['status']}; {CACHE_HEADER} "
          + (f"present ({call['key']})" if call["key"] is not None else "absent")
          + (f"; completion tokens {call['usage'].get('completion_tokens')}" if call["status"] == 200 else "")
          + f"; cache fields {json.dumps(call['cache_fields'], default=str) if call['cache_fields'] else 'none'}"
          + (f"\n    answer: {call['text']!r}" if call["status"] == 200 else f"\n    error: {str(call['text'])[:500]}"))


def main() -> None:
    p = argparse.ArgumentParser(prog="py helpers/check_answer_cache.py",
                                description="Whether NASA's LiteLLM answers repeated requests from its own cache.")
    p.add_argument("--model", default=llm.MODEL, help=f"the model to ask (default: {llm.MODEL})")
    args = p.parse_args()
    at = tag()
    print(f"The question, sent 4 times: {question(at)!r}\nCalls 1 and 2 as they are; calls 3 and 4 with "
          f"{json.dumps(CONTROL)}.\n{RULE}")
    llm.confirm(f"Ask {args.model} this question {len(CALLS)} times ({len(CALLS)} tiny paid calls, a sentence each)? "
                f"Press Enter to go ahead, or anything else to cancel.")
    calls = []
    for name, extra in CALLS:
        calls.append(ask(args.model, question(at), extra))
        show(name, calls[-1])
    found, why = verdict(calls)
    taken, words = accepted(calls)
    print(f"\nVerdict: {found}: {why}.\nThe cache control: {words}.\n{advice(found, taken)}"
          f"\n\nPut these lines in docs/findings.md.")


if __name__ == "__main__":
    main()
