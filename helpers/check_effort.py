"""
helpers/check_effort.py -- does NASA's LiteLLM pass an effort setting on to Claude?

    py helpers/check_effort.py                           both steps, claude-opus-5.5 (the default model)
    py helpers/check_effort.py --only a                  step A only (an invalid value)
    py helpers/check_effort.py --only b                  step B only (a question that needs reasoning)
    py helpers/check_effort.py --model <name>            another Claude model

On Claude Opus 5.5, adaptive thinking is always on: the model decides whether
and how much to think on each request, and the effort setting is the main
control of how much (Anthropic: "Adaptive thinking is always on and can't be
turned off, so effort is the primary control for how much the model reasons",
https://platform.claude.com/docs/en/build-with-claude/effort; "At lower levels,
Claude can skip thinking entirely for simpler problems", same page). The
pipeline sends Claude no effort, so it runs at the model's default (medium:
common/common_helpers/llm.py, DEFAULT_EFFORT). Before the pipeline sets an
effort itself, this check finds out whether LiteLLM forwards one. It answers
in two steps.

Step A: an invalid value. Two requests, one with LiteLLM's `reasoning_effort`
set to "not_a_level", one with Anthropic's own `output_config` {"effort":
"not_a_level"}. A setting that is passed on reaches a check that refuses it:
LiteLLM's docs say any value but the listed ones "will raise a validation
error" (https://docs.litellm.ai/docs/providers/anthropic_effort), and Anthropic
answers a request whose content is invalid with HTTP 400 invalid_request_error
(https://platform.claude.com/docs/en/api/errors). So a refusal (4xx) means the
setting is read, not dropped; an answer (HTTP 200) means LiteLLM dropped or
ignored it (its drop_params option drops a setting without saying so). The
error text, printed in full, says whose check refused it. Expected cost: none.
A refused request produces no answer and reports no tokens, and both services
bill by the token; neither says in so many words that a refused request is
unbilled. A request that is answered instead is a tiny paid call (a one-word
answer), so step A asks before sending.

Step B: a question that needs several steps of reasoning (a counting puzzle
whose answer, 168, was checked by listing every arrangement), asked 3 times
each with no effort, with `reasoning_effort` "low" and with "high": 9 paid
calls, asked about before paying. Anthropic counts thinking inside the billed
output tokens ("monitor the usage.output_tokens_details.thinking_tokens field
in the response, which reports how many of the billed output tokens were
internal reasoning", https://platform.claude.com/docs/en/build-with-claude/extended-thinking),
and LiteLLM reports them as completion tokens. So completion tokens are the
measure, even where the service reports 0 reasoning tokens. The decision rule
is fixed before the calls and printed first: "passed on" if every high call
used more completion tokens than every low call, or the mean of high is at
least 1.5 times the mean of low; "not shown" otherwise, and also when a call
failed. Each answer is checked against 168.

Needs the NASA network and your key in .env (docs/running_on_nasa_laptop.md).
Not a pipeline step: it writes nothing. Put what it prints in docs/findings.md.
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common import llm

# ------------------------------ step A ------------------------------------

#: A value no service takes as an effort level.
INVALID = "not_a_level"

#: Step A's requests: a name for the printout, and what is added to the request.
STEP_A = (("reasoning_effort " + INVALID, {"reasoning_effort": INVALID}),
          ("output_config effort " + INVALID, {"output_config": {"effort": INVALID}}))

#: Step A's question: a one-word answer, so a request that is answered costs as little as a request can.
STEP_A_QUESTION = "Reply with the word OK only."


def step_a_verdict(status: int, text: str) -> str:
    """What one step A reply shows, in words. status: the HTTP status; text: the service's error text, or the
    answer."""
    if 400 <= status < 500:
        return (f"refused (HTTP {status}), so the setting is read, not dropped. The error text, which says whose "
                f"check refused it: {text}")
    if status == 200:
        return ("answered (HTTP 200), so the setting was dropped or ignored on the way: an invalid value that "
                f"reached a check would have been refused. The answer: {text!r}")
    return f"no verdict: HTTP {status}, which says nothing about the setting; run the check again. {text}"


# ------------------------------ step B ------------------------------------

#: A question that needs several steps of reasoning, with an answer that can be checked: 168, found by listing all
#: 720 arrangements (the A-before-B, C-not-next-to-D and E-not-at-an-end conditions leave 168).
PUZZLE = ("How many arrangements of the six letters A, B, C, D, E, F in a row have A somewhere before B, C not next "
          "to D, and E in neither end position? Work it out, then give the number alone on the last line.")
PUZZLE_ANSWER = 168

#: Step B's settings: a name for the printout, and what is added to the request.
STEP_B = (("no effort sent", {}),
          ("reasoning_effort low", {"reasoning_effort": "low"}),
          ("reasoning_effort high", {"reasoning_effort": "high"}))

#: How many times step B asks each setting.
REPEATS = 3

#: The decision rule's second test: the mean of high at least this many times the mean of low.
RATIO = 1.5

RULE = ("Decision rule (fixed before the calls): \"passed on\" if every high call uses more completion tokens than "
        f"every low call, or the mean of high is at least {RATIO} times the mean of low; \"not shown\" otherwise, and "
        "also when a call failed. Completion tokens are the measure: Anthropic counts thinking inside the billed "
        "output tokens, so they include the thinking even when the service reports 0 reasoning tokens.")


def answer_number(text) -> int | None:
    """The number on an answer's last line that has one (the puzzle asks for it there), or None."""
    for line in reversed(str(text or "").strip().splitlines()):
        numbers = re.findall(r"\d[\d,]*", line)
        if numbers:
            return int(numbers[-1].replace(",", ""))
    return None


def step_b_verdict(low: list, high: list) -> tuple:
    """("passed on" or "not shown", the reason) for the completion tokens of the low and the high calls; a call that
    failed is None."""
    if len(low) < REPEATS or len(high) < REPEATS or None in low or None in high:
        return "not shown", f"a call failed, so the {REPEATS} low and {REPEATS} high counts the rule needs aren't all there"
    mean_low, mean_high = statistics.mean(low), statistics.mean(high)
    if min(high) > max(low):
        return "passed on", f"every high call ({min(high)} or more) used more than every low call ({max(low)} or fewer)"
    if mean_high >= RATIO * mean_low:
        return "passed on", f"the mean of high ({mean_high:.0f}) is at least {RATIO} times the mean of low ({mean_low:.0f})"
    return "not shown", (f"the high and low counts overlap (high from {min(high)}, low up to {max(low)}), and the mean "
                         f"of high ({mean_high:.0f}) is less than {RATIO} times the mean of low ({mean_low:.0f})")


# ------------------------------ the requests -------------------------------

def ask(model: str, question: str, extra: dict) -> tuple:
    """One request through LiteLLM: (HTTP status, the answer or the service's error text, usage)."""
    url, headers = llm._litellm("/v1/chat/completions")
    payload = {"model": model, "messages": [{"role": "user", "content": question}],
               "max_tokens": llm.MAX_ANSWER_TOKENS, **extra}
    resp = llm._post(url, headers=headers, json=payload, timeout=(5, llm.READ_TIMEOUT))
    if resp.status_code >= 400:
        return resp.status_code, resp.text, {}
    body = resp.json()
    answer = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
    return resp.status_code, answer, body.get("usage") or {}


def step_a(model: str) -> None:
    llm.confirm(f"Step A: send {model} {len(STEP_A)} requests with an invalid effort value. Expected: both refused, "
                f"which costs nothing; a request that is answered instead is a tiny paid call. Press Enter to go "
                f"ahead, or anything else to cancel.")
    print("\nStep A: an invalid effort value. Refused (4xx) = the setting is read; answered (200) = dropped or ignored.")
    for name, extra in STEP_A:
        status, text, usage = ask(model, STEP_A_QUESTION, extra)
        print(f"  {name}: {step_a_verdict(status, text)}" + (f" Usage: {json.dumps(usage)}" if usage else ""))


def step_b(model: str) -> None:
    calls = len(STEP_B) * REPEATS
    print(f"\nStep B: the puzzle (expected answer {PUZZLE_ANSWER}), {REPEATS} times at each of: "
          f"{', '.join(n for n, _ in STEP_B)}.\n{RULE}")
    llm.confirm(f"Ask {model} the puzzle {calls} times ({calls} paid calls, each up to a few thousand tokens at high "
                f"effort)? Press Enter to go ahead, or anything else to cancel.")
    tokens = {}
    for name, extra in STEP_B:
        tokens[name] = []
        for i in range(1, REPEATS + 1):
            status, text, usage = ask(model, PUZZLE, extra)
            if status != 200:
                tokens[name].append(None)
                print(f"  {name}, call {i}: failed, HTTP {status}: {str(text)[:300]}")
                continue
            completion = usage.get("completion_tokens")
            tokens[name].append(completion)
            got = answer_number(text)
            print(f"  {name}, call {i}: completion tokens {completion}; reasoning tokens reported "
                  f"{llm.reasoning_tokens(usage)}; answer {got} ("
                  + ("correct" if got == PUZZLE_ANSWER else f"wrong, expected {PUZZLE_ANSWER}") + ")")
        counts = [t for t in tokens[name] if t is not None]
        print(f"  {name}: mean completion tokens "
              + (f"{statistics.mean(counts):.0f}" if counts else "none (every call failed)"))
    verdict, why = step_b_verdict(tokens["reasoning_effort low"], tokens["reasoning_effort high"])
    print(f"\nStep B's verdict: {verdict}: {why}.")


def main() -> None:
    p = argparse.ArgumentParser(prog="py helpers/check_effort.py",
                                description="Whether LiteLLM passes an effort setting on to a Claude model.")
    p.add_argument("--model", default=llm.MODEL, help=f"the Claude model to check (default: {llm.MODEL})")
    p.add_argument("--only", choices=("a", "b"), help="run only step A (an invalid value) or step B (the puzzle)")
    args = p.parse_args()
    if args.only != "b":
        step_a(args.model)
    if args.only != "a":
        step_b(args.model)
    print("\nPut these lines in docs/findings.md.")


if __name__ == "__main__":
    main()
