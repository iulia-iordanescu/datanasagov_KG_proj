"""
helpers/check_effort.py -- does NASA's LiteLLM pass an effort setting on to Claude?

    py helpers/check_effort.py                           claude-opus-5.5 (the default model)
    py helpers/check_effort.py --model <name>            another Claude model

Claude Opus 5.5 always thinks, and its effort setting decides how much
(Anthropic: https://platform.claude.com/docs/en/build-with-claude/effort).
The pipeline sends Claude no effort, so it runs at the model's default
(medium: common/common_helpers/llm.py, DEFAULT_EFFORT). Before the pipeline
sets an effort itself, this check finds out whether LiteLLM forwards one.

It asks the same small question four ways: with no effort, then with
LiteLLM's `reasoning_effort` at "low" and at "high", then with Anthropic's
own `output_config` {"effort": "high"} passed through. For each it prints
whether the service accepted it, and the answer and thinking tokens it
reported. If "high" spends clearly more tokens than "low", the setting
reaches the model; if all four spend about the same, it doesn't.

Four tiny paid calls; it asks before paying. Needs the NASA network and
your key in .env (docs/running_on_nasa_laptop.md). Not a pipeline step: it
writes nothing. Put what it prints in docs/findings.md.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # the repository folder, for common/

from common import llm

#: A question short to answer but worth some thinking, so the effort shows in the token counts.
QUESTION = ("A train leaves at 09:47 and arrives at 14:12 the same day, stopping 3 times for 6 minutes each. "
            "How many minutes is it moving? Answer with the number only.")

#: The four requests: a name for the printout, and what is added to the request.
WAYS = (("no effort sent", {}),
        ("reasoning_effort low", {"reasoning_effort": "low"}),
        ("reasoning_effort high", {"reasoning_effort": "high"}),
        ("output_config effort high", {"output_config": {"effort": "high"}}))


def ask(model: str, extra: dict) -> str:
    """One request through LiteLLM; a line saying what came back."""
    url, headers = llm._litellm("/v1/chat/completions")
    payload = {"model": model, "messages": [{"role": "user", "content": QUESTION}],
               "max_tokens": llm.MAX_ANSWER_TOKENS, **extra}
    resp = llm._post(url, headers=headers, json=payload, timeout=(5, llm.READ_TIMEOUT))
    if resp.status_code >= 400:
        return f"refused, HTTP {resp.status_code}: {llm._litellm_error(resp)}"
    body = resp.json()
    usage = body.get("usage") or {}
    details = usage.get("completion_tokens_details")
    thinking = details.get("reasoning_tokens") if isinstance(details, dict) else None
    answer = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
    return (f"accepted; answer {answer!r}; answer tokens {usage.get('completion_tokens')}; thinking tokens "
            + ("not reported" if thinking is None else str(thinking))
            + f"; answered as {body.get('model')}; usage {json.dumps(usage)}")


def main() -> None:
    p = argparse.ArgumentParser(prog="py helpers/check_effort.py",
                                description="Whether LiteLLM passes an effort setting on to a Claude model.")
    p.add_argument("--model", default=llm.MODEL, help=f"the Claude model to check (default: {llm.MODEL})")
    model = p.parse_args().model
    llm.confirm(f"Ask {model} through LiteLLM one small question {len(WAYS)} ways ({len(WAYS)} tiny paid calls)? "
                f"Press Enter to go ahead, or anything else to cancel.")
    for name, extra in WAYS:
        print(f"  {name}: {ask(model, extra)}")
    print("\nIf 'reasoning_effort high' used clearly more tokens than 'low', LiteLLM passes the setting on. "
          "Put these lines in docs/findings.md.")


if __name__ == "__main__":
    main()
