"""
common/common_helpers/llm_paid.py -- a paid run.

A part of common/common_helpers/llm.py: PaidCalls (asks once before a run's first paid call, showing any notes about
the run first; makes a one-line test call and checks its token counts; counts the calls, shows their progress,
records each failed call, and stops early when the first calls fail), Calls and paid_calls (what a step's stages
share: PaidCalls and the folder its answers are cached in), run_parallel (runs jobs a few at a time; Ctrl-C cancels
those not yet started), the advice a failed call's messages give, and confirm (the stop itself). The early stop's
numbers are llm.py's settings. Import these names from common.llm, never from this file.
"""

import datetime as dt
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from common import llm
from common.audit import log
from common.files import append_text
from common.stop import Stop
from common.llm import (
    DIRECT_SERVICES, EARLY_STOP_FAILURES, EARLY_STOP_WINDOW, PROGRESS_ESTIMATE_AFTER, PROGRESS_SECONDS,
    READ_TIMEOUT, REASKS, REQUESTS, SERVED, SERVICES, THINKING_LEVELS, THINKING_WARN_SHARE, _last, call_settings,
    maker, max_tokens_sent, takes_thinking_cap, thinking_parameter, thinking_sent)
from common.llm_errors import (
    BUDGET_GONE, BadReply, BudgetExhausted, CutOff, FORBIDDEN, ModelCallForbidden, Refused, _forbidden_message)
from common.llm_replies import reasoning_tokens
from common.llm_calls import TEST_PROMPT


#: This run's failed model calls: how many failed, how many of them were cut off, how many weren't made because of the
#: early stop, and the file that describes each (failed_calls_file), for the report and the run's last lines.
#: Reset by paid_calls.
OUTCOMES = {"failed": 0, "cut_off": 0, "not_sent": 0, "file": None}


#: Warnings found while the run paid (the test call's check), for the report's Warnings (common/common_helpers/step.py).
RUN_WARNINGS = []


class EarlyStop(SystemExit):
    """The early stop (EARLY_STOP_FAILURES of the first EARLY_STOP_WINDOW calls failed). A SystemExit, so the step
    stops with its report and log; run_parallel first lets the calls already under way finish and keeps their
    answers."""

    def __init__(self, message: str, paid):
        super().__init__(message)
        self.paid = paid


def _lower_thinking() -> str | None:
    """How to leave the answer more of MAX_ANSWER_TOKENS by thinking less, with this run's settings; None when the
    pipeline can't cap this model's thinking."""
    sent = thinking_sent()
    if sent and sent != "low":
        lower = " or ".join(f"`--thinking {t}`" for t in reversed(THINKING_LEVELS[:THINKING_LEVELS.index(sent)]))
        return f"set the step's thinking setting lower (it is {sent}; {lower})"
    if llm.THINKING == "model_default" and takes_thinking_cap():
        return "give `--thinking low` (the thinking isn't capped: thinking is model_default)"
    return None


def cut_off_advice(usage=None) -> str:
    """What to change after an answer was cut off at MAX_ANSWER_TOKENS (or a test call thought too much), from the
    token counts the service reported, not from the settings: thinking took most of the tokens, the answer itself is
    long, or the service didn't say how many were thinking."""
    usage = usage if isinstance(usage, dict) else {}
    if max_tokens_sent() is None:
        return ("Ask Sage takes no answer limit (MAX_ANSWER_TOKENS isn't sent), so the model's own limit cut the "
                "answer: lower the step's max_chars so each text piece asks for fewer facts, choose another model "
                "(`--model`), or run through LiteLLM (`--service litellm`), which takes the limit")
    details = usage.get("completion_tokens_details")
    reported = isinstance(details, dict) and details.get("reasoning_tokens") is not None
    thought, total = reasoning_tokens(usage), usage.get("completion_tokens")
    limit = f"MAX_ANSWER_TOKENS in common/common_helpers/llm.py (now {llm.MAX_ANSWER_TOKENS:,})"
    shorter = f"raise {limit}, or, when the text piece is long, lower the step's max_chars so each answer is shorter"
    if not reported:
        lower = _lower_thinking()
        got = f" (the answer got {total:,} tokens in all)" if isinstance(total, int) else ""
        return (f"Thinking tokens not reported; can't tell which used the {llm.MAX_ANSWER_TOKENS:,} tokens, the model's "
                f"thinking or the answer itself{got}: "
                + (f"if the model thinks, {lower}, so more of the tokens are left for the answer; if not, " if lower
                   else "") + shorter)
    if thought >= THINKING_WARN_SHARE * llm.MAX_ANSWER_TOKENS:
        sent = thinking_sent()
        if sent == "low":
            fix = (f"the thinking is already at its lowest cap (low): raise {limit} and give `--thinking "
                   f"model_default`, or choose another model (`--model`)")
        else:
            fix = _lower_thinking()
            fix = (f"{fix}, so more of the tokens are left for the answer" if fix else
                   f"the pipeline can't cap this model's thinking: raise {limit}, or choose another model (`--model`)")
        return (f"Thinking used most of the tokens: the model spent {thought:,} of the {llm.MAX_ANSWER_TOKENS:,} tokens "
                f"thinking, leaving {llm.MAX_ANSWER_TOKENS - thought:,} for the answer; {fix}")
    answer = f" and {total - thought:,} on the answer" if isinstance(total, int) else ""
    return (f"The answer itself is long: the model spent {thought:,} of the {llm.MAX_ANSWER_TOKENS:,} tokens thinking"
            f"{answer}; {shorter}")


def advice(error) -> str:
    """What to do about one failed call, in words: the same advice the messages and the failed-call record give."""
    if isinstance(error, BudgetExhausted):
        return ("Ask the administrators of the service to raise or reset the budget; nothing to retry before that "
                "(docs/running_on_nasa_laptop.md, *The budget is used up*)")
    if isinstance(error, CutOff):
        return cut_off_advice(getattr(error, "usage", None))
    if isinstance(error, Refused):
        return ("Asking again gets the same answer. Look at the record's text; if refusals (the service's filter, or "
                "the model declining in prose) come often with this model, choose another (`--model`)")
    if "no answer within" in str(error):
        return "Run the step again later; if it keeps happening, lower the step's max_chars"
    if isinstance(error, BadReply):
        return ("Read the answer (in the failed-call record or the log) to see what the model wrote instead of the "
                "JSON object; if this model keeps doing it, choose another (`--model`)")
    return ("Read the error: rate limits and server errors usually pass, so run the step again; if it keeps failing, "
            "check the connection and the key in .env")


def failed_calls_file() -> Path | None:
    """outputs/logs/<run id>_failed_calls.jsonl, beside the run's log; None outside a run."""
    from common.audit import current_run_id
    from common.step import LOGS_DIR
    run_id = current_run_id()
    return LOGS_DIR / f"{run_id}_failed_calls.jsonl" if run_id else None


def _usage_counts(usage) -> dict:
    usage = usage if isinstance(usage, dict) else {}
    return {"prompt_tokens": usage.get("prompt_tokens"), "answer_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": reasoning_tokens(usage) if usage else None}


def _duration(seconds: float) -> str:
    return f"{seconds:.0f} s" if seconds < 90 else f"{seconds / 60:.0f} min" if seconds < 5400 else f"{seconds / 3600:.1f} h"


class PaidCalls:
    """Asks once, just before a run's first paid call; checks the test call; counts the calls, shows their progress,
    records each failed one, and stops the run early when its first calls fail.

    A stage calls start(plan) before it makes any call a cache couldn't answer, expect(n) before n calls, and, as each
    call ends, made_call() (when it answered) and outcome(where, prompt, error). The first start() logs the plan,
    asks the person to press Enter (unless confirm is False, for runs with nobody at the keyboard), and makes one tiny
    test call, so a wrong model name or key fails once here instead of once per text; its token counts are checked
    (an answer cut off, or thinking that leaves too little room, is said before paying for more). A run whose every
    answer comes from the cache never asks and never pays. Declining exits the run having spent nothing.

    outcome() prints the progress (at most every PROGRESS_SECONDS), writes a failed call to the run's failed-call
    record (failed_calls_file), and raises EarlyStop when EARLY_STOP_FAILURES of the first EARLY_STOP_WINDOW calls
    failed.

    notes: what the step found, BEFORE any call, that differs from what the
    person asked for (an id that isn't in the catalog, fewer texts than
    asked, …), one sentence each. start() shows them above the question, so
    the person can cancel and fix the request before paying; the step also
    puts them in its report's warnings, where they're read on runs that
    needed no call or had nobody at the keyboard."""

    def __init__(self, confirm: bool, notes: list = (), step: str = "", command: str | None = None):
        self.confirm = confirm
        self.notes = list(notes)
        self.step = step                    # the step's folder name, e.g. 070_evaluate
        self.command = command or (f"py {step}/run.py" if step else "")   # how messages say to run it again
        self.started = False
        self.made = 0                       # calls made by the stages
        self.test_calls = 0                 # 1 once the run has started paying
        self._lock = threading.Lock()
        self.clock = time.monotonic         # replaced by the tests
        self.ended = 0                      # calls the early stop watches, ended this run, answered or failed
        self.failures = []                  # (where, error) of each of those that failed
        self.stopped = False
        self._batch = {"total": None, "done": 0, "failed": 0, "cut": 0, "began": 0.0, "shown": None}

    def start(self, plan: str, to_pay: int | None = None) -> None:
        """plan: what the run will ask, in words; to_pay: how many model calls it will pay for (those the cache can't
        answer), shown in the question itself, so the count is read before Enter. None only where a stage can't
        count them before its first answer."""
        if self.started:
            return
        if FORBIDDEN["why"] is not None:                    # a free command: stop before the question and the test call
            raise ModelCallForbidden(_forbidden_message(
                f"{self.step or 'This run'} would pay for "
                + (f"{to_pay:,} model call(s) the cache can't answer" if to_pay is not None else "model calls")
                + f" ({plan.strip().rstrip('.')})"))
        log.info(plan)
        log.info(f"model: {llm.MODEL}, through {SERVICES.get(llm.SERVICE, llm.SERVICE)}"
                 + (f", thinking {thinking_sent()}" if thinking_sent() else ""))
        if self.notes:
            show_warnings(self.step, self.notes)
        count = (f"{to_pay:,} model call(s) to pay for, and 1 test call first" if to_pay is not None
                 else "1 test call first")
        if self.confirm:
            llm.confirm(f"Press Enter to start ({count}), or anything else to cancel."
                    if not self.notes else
                    f"Press Enter to go ahead anyway ({count}), or anything else to cancel.")
        again = f"`{self.command}`" if self.command else "the step"
        service = SERVICES.get(llm.SERVICE, llm.SERVICE)
        try:
            llm.call_llm(TEST_PROMPT, attempts=2)
        except Exception as e:                              # noqa: BLE001
            OUTCOMES["failed"] += 1
            OUTCOMES["cut_off"] += isinstance(e, CutOff)
            self._record({"stage": "test call"}, TEST_PROMPT, e)
            self._test_call_failed(e, again, service)
        self.started = True
        self.test_calls = 1
        self._check_test_call()

    def _test_call_failed(self, e: Exception, again: str, service: str) -> None:
        """Stop the run: the test call failed (e), so no other call is made."""
        file = f" The call is described in {OUTCOMES['file']}." if OUTCOMES["file"] else ""
        if isinstance(e, CutOff):
            sys.exit(f"Test call to {llm.MODEL} through {service} was cut off at the longest length allowed "
                     f"({llm.MAX_ANSWER_TOKENS:,} tokens) on a one-line answer, so no other model call was made: every "
                     f"answer of this run would be cut off too. {cut_off_advice(getattr(e, 'usage', None))}; then run "
                     f"{again} again.{file}")
        sys.exit(f"Test call to {llm.MODEL} through {service} failed ({e}), so no other model "
                 f"call was made. If {service} says the model "
                 f"isn't allowed, give another with --model <name> (`py helpers/models.py --service {llm.SERVICE} --try <name> ...` "
                 f"tells which you may use)"
                 + (f"; if it names {thinking_parameter()}, give `--thinking model_default`, which sends no thinking "
                    f"cap" if thinking_sent() else "")
                 + f"; otherwise check your key in .env and that you're on NASA's network. Then run {again} again.{file}")

    def _check_test_call(self) -> None:
        """One line on the test call's token counts, and a stop to think when its thinking leaves too little room."""
        reply = getattr(_last, "reply", None) or {}
        usage = reply.get("usage") or {}
        if not usage:
            log.info(f"  test call: ok ({SERVICES.get(llm.SERVICE, llm.SERVICE)} reports no token counts)")
            return
        thought = reasoning_tokens(usage)
        answer = (usage.get("completion_tokens") or 0) - thought
        log.info(f"  test call: ok (answer {answer:,} tokens, thinking "
                 + (f"{thought:,} tokens)" if "completion_tokens_details" in usage else "not reported)"))
        if thought < THINKING_WARN_SHARE * llm.MAX_ANSWER_TOKENS:
            return
        note = (f"The test call's one-line answer used {thought:,} tokens thinking, {thought / llm.MAX_ANSWER_TOKENS:.0%} "
                f"of the {llm.MAX_ANSWER_TOKENS:,} tokens each answer may use (MAX_ANSWER_TOKENS in "
                f"common/common_helpers/llm.py), so a record's longer answer is likely to be cut off. "
                f"{cut_off_advice(usage)}.")
        RUN_WARNINGS.append(note)
        show_warnings(self.step, [note])
        if self.confirm:
            llm.confirm("Press Enter to go ahead anyway, or anything else to cancel (only the test call was paid for).",
                    spent="Only the test call was paid for.")

    def expect(self, total: int) -> None:
        """The next total calls are one stage's: its progress lines count them."""
        with self._lock:
            self._batch = {"total": total, "done": 0, "failed": 0, "cut": 0, "began": self.clock(), "shown": None}

    def made_call(self) -> None:
        with self._lock:                    # stages may call from several threads
            self.made += 1

    def outcome(self, where: dict, prompt: str, error: Exception | None = None, watched: bool = True) -> None:
        """One paid call ended: answered (error None) or failed. Shows the progress, records a failed call, and
        raises EarlyStop when too many of the run's first calls failed. where: {"stage", "record", "text_piece"}, as
        much as the stage knows. watched: whether the early stop counts the call; False for the stages that ask one
        prompt at a time (common/common_helpers/cache.py, ask_cached), which are few, and where a failure is often
        expected and handled (040's labeling asks a refused batch again in halves, to find the item refused)."""
        with self._lock:
            b = self._batch
            if not b["began"]:
                b["began"] = self.clock()
            b["done"] += 1
            self.ended += watched
            if error is not None:
                b["failed"] += 1
                b["cut"] += isinstance(error, CutOff)
                if watched:
                    self.failures.append((where, error))
                OUTCOMES["failed"] += 1
                OUTCOMES["cut_off"] += isinstance(error, CutOff)
                self._record(where, prompt, error)
            self._progress()
            early = (watched and not self.stopped and self.ended <= EARLY_STOP_WINDOW
                     and len(self.failures) >= EARLY_STOP_FAILURES)
            if early:
                self.stopped = True
        if early:
            raise EarlyStop(self._early_stop_message(), self)

    def _progress(self) -> None:
        b, now = self._batch, self.clock()
        last = b["total"] is not None and b["done"] >= b["total"]
        if not (b["shown"] is None or last or now - b["shown"] >= PROGRESS_SECONDS):
            return
        b["shown"] = now
        failed = f"{b['failed']:,} failed" + (f" ({b['cut']:,} cut off)" if b["cut"] else "")
        if b["total"] is None:
            log.info(f"  model calls: {b['done']:,} done, {failed}")
            return
        if last:
            left = f"took {_duration(now - b['began'])}"
        elif b["done"] < PROGRESS_ESTIMATE_AFTER:
            left = "estimating the time left…"
        else:
            left = f"about {_duration((now - b['began']) / b['done'] * (b['total'] - b['done']))} left"
        log.info(f"  model calls: {b['done']:,} of {b['total']:,} done, {failed}, {left}")

    def _early_stop_message(self) -> str:
        what = [f"{w.get('record', w.get('stage', '?'))}"
                + (f" piece {w['text_piece']}" if w.get("text_piece") else "") + f": {e}" for w, e in self.failures]
        cut = [e for _, e in self.failures if isinstance(e, CutOff)]
        todo = cut_off_advice(max((getattr(e, "usage", None) or {} for e in cut), key=reasoning_tokens)) if cut \
            else advice(self.failures[-1][1])
        file = OUTCOMES["file"]
        return (f"Step {self.step.split('_')[0]} stopped early: {len(self.failures)} of the first {self.ended} model "
                f"calls of this run failed ({'; '.join(what)}), so it made no more: the rest would most likely fail "
                f"the same way and be paid for nothing (the early stop: {EARLY_STOP_FAILURES} failed among the first "
                f"{EARLY_STOP_WINDOW}, in common/common_helpers/llm.py). What to do: {todo}."
                + (f" Each failed call is described in {file}." if file else "")
                + f" Answers already received are kept in the cache, so the next run pays only for the rest: run "
                  f"`{self.command}` again once that is changed.")

    def not_sent(self, jobs: list) -> None:
        """The calls the early stop prevented, [(where, prompt)]: one line each in the failed-call record."""
        with self._lock:
            for where, prompt in jobs:
                OUTCOMES["not_sent"] += 1
                self._record(where, prompt, None)

    def _record(self, where: dict, prompt: str, error: Exception | None) -> None:
        """One line of the failed-call record: everything needed to see why the call failed (never a key)."""
        path = failed_calls_file()
        if path is None:
            return
        usage = getattr(error, "usage", None)
        entry = {"time": dt.datetime.now().astimezone().isoformat(timespec="seconds"), "step": self.step,
                 "run_id": path.name.removesuffix("_failed_calls.jsonl"), **where,
                 "outcome": "not_sent" if error is None else "cut_off" if isinstance(error, CutOff) else "failed",
                 "service": llm.SERVICE, "model": llm.MODEL,
                 "call_settings": {**call_settings(), "read_timeout_s": READ_TIMEOUT},
                 "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                 "prompt_characters": len(prompt)}
        if error is None:
            entry["why"] = ("not made: the service answered that the budget is used up, so the run stopped before "
                            "this call" if BUDGET_GONE["error"] is not None else
                            "not made: the early stop stopped the run before this call")
        else:
            call = getattr(error, "call", None) or {}
            usage = usage or call.get("usage")
            entry.update({"finish_reason": getattr(error, "finish_reason", None) or call.get("finish_reason"),
                          "native_finish_reason": call.get("native_finish_reason"), **_usage_counts(usage),
                          "usage": usage or None, "http_status": call.get("http_status"),
                          "error_body": call.get("error_body"), "error_type": type(error).__name__,
                          "cause_type": call.get("cause_type"), "error": str(error),
                          "settings_sent": call.get("settings_sent"), "request_bytes": call.get("request_bytes"),
                          "served_as": call.get("served_as"), "attempts": call.get("attempts"),
                          "asks": call.get("asks"), "seconds": call.get("seconds"),
                          "answer": getattr(error, "answer", None), "what_to_do": advice(error)})
        append_text(path, json.dumps(entry, ensure_ascii=False) + "\n")
        OUTCOMES["file"] = path.relative_to(path.parents[2]).as_posix()


@dataclass
class Calls:
    """What a step's model-calling stages share: the confirmation-and-count
    (PaidCalls) and the folder that keeps every answer (common/common_helpers/cache.py)."""
    paid: PaidCalls
    cache_dir: Path


def paid_calls(settings: dict, output, notes: list = (), session_id: str | None = None,
               command: str | None = None) -> Calls:
    """The Calls of one run: uses the model the setting `model` names, through the service the setting `service`
    names, with the thinking cap the setting `thinking` gives; asks before paying (setting confirm_paid_calls),
    showing notes first; answers kept in cache/ inside the step's output folder. A setting it can't use stops the
    step (Stop: `stopped`, a problem the person can fix). session_id: sent with each LiteLLM request of the run
    (SESSION_ID); None sends none. command: how messages say to run it again (a helper's, e.g. py helpers/second_opinion.py;
    a step leaves it out: py <step>/run.py)."""
    from common.step import check_settings                  # the one check of every setting (common.step.shared_specs)
    given = {"service": settings.get("service") if settings.get("service") is not None else llm.SERVICE,
             "model": settings.get("model"), "thinking": settings.get("thinking") if settings.get("thinking") is not None else llm.THINKING,
             "repeat": settings.get("repeat", 1)}
    check_settings({k: v for k, v in given.items() if k != "model" or v is not None}, {})
    service, thinking = str(given["service"]).strip().lower(), str(given["thinking"]).strip().lower()
    name = str(given["model"] or "").strip()
    if not name:
        raise Stop(f"The setting model must be a text (not empty), but is {given['model']!r}, so the step can't run. "
                   f"Give --model <name> (`py helpers/models.py` lists them), then run the step again.")
    own = DIRECT_SERVICES.get(service, {}).get("maker")
    if own and maker(name) and maker(name) != own:
        raise Stop(f"The setting model is {name}, a model by {maker(name)}, but the setting service is {service}, "
                   f"which reaches only {own}'s models ({SERVICES[service]}), so the step can't run. Give a model by "
                   f"{own} (`py helpers/models.py --service {service}` lists them), or a service that reaches {name} "
                   f"(e.g. --service litellm), then run the step again.")
    repeat = given["repeat"]
    llm.MODEL, llm.SERVICE, llm.THINKING, llm.REPEAT, llm.SESSION_ID = name, service, thinking, repeat, session_id
    SERVED.clear()
    for k in REQUESTS:
        REQUESTS[k] = 0
    for k in REASKS:
        REASKS[k] = 0
    OUTCOMES.update(failed=0, cut_off=0, not_sent=0, file=None)
    RUN_WARNINGS.clear()
    return Calls(paid=PaidCalls(confirm=settings["confirm_paid_calls"], notes=notes, step=Path(output).name, command=command),
                 cache_dir=Path(output) / "cache")


def run_parallel(fn, jobs: dict, workers: int, handle, stop_note: str, not_sent=None) -> None:
    """Run fn(*args) for every (key, args) in jobs, workers at a time, and
    call handle(n, key, result, error) in this thread as each finishes (n
    counts from 1; error is None on success, result None on failure).

    Ctrl+C cancels every call not yet started, so a stopped run spends
    nothing more than what is already in flight, then raises Interrupted with stop_note.
    Calls already in flight cannot be recalled; their results are not
    handled.

    When handle raises EarlyStop (PaidCalls.outcome), every call not yet started is cancelled, the calls already under
    way are waited for and handled (so their paid answers are kept), not_sent(keys of the cancelled jobs) is called,
    and the EarlyStop goes on. A used-up budget (BudgetExhausted, raised by a call) is met the same way: the calls under
    way are handled, not_sent gets every call never sent, and the BudgetExhausted goes on (also when it came while an
    early stop was waiting for the calls under way: then no other call can be made at all)."""
    pool = ThreadPoolExecutor(workers)
    futures, handled = {}, set()
    try:
        futures = {pool.submit(fn, *args): key for key, args in jobs.items()}
        for n, future in enumerate(as_completed(futures), 1):
            try:
                result, error = future.result(), None
            except Exception as e:                      # noqa: BLE001
                result, error = None, e
            handled.add(future)
            handle(n, futures[future], result, error)
    except (EarlyStop, BudgetExhausted) as stop:
        # Nothing more is started. The calls already under way are waited for and handled, so their paid answers are
        # kept; a used-up budget (BudgetExhausted) met among them is the stop said, since nothing more can be sent.
        cancelled = [f for f in futures if f.cancel()]
        under_way = [f for f in futures if f not in handled and f not in cancelled]
        unsent = list(cancelled)
        for n, future in enumerate(under_way, len(handled) + 1):
            try:
                result, error = future.result(), None
            except Exception as e:                      # noqa: BLE001
                result, error = None, e
            except BudgetExhausted as e:
                stop = e if isinstance(stop, EarlyStop) else stop
                if not e.answered:                      # stopped before it was sent
                    unsent.append(future)
                    continue
                result, error = None, e                 # the call the service answered with the used-up budget
            try:
                handle(n, futures[future], result, error)
            except EarlyStop:
                pass                                    # the run is stopping already: one message
        if not_sent is not None:
            not_sent([futures[f] for f in unsent])
        raise stop
    except KeyboardInterrupt:
        pool.shutdown(wait=False, cancel_futures=True)
        raise Interrupted(f"Stopped with Ctrl+C. Model calls not yet started were cancelled, so they cost nothing. "
                          f"{stop_note}") from None
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def warning_list(step: str, notes: list) -> str:
    """'Step 070 found 2 warnings:', then the notes numbered; a note's further
    lines are indented under it."""
    head = f"Step {step.split('_')[0]} found {len(notes)} warning{'s' if len(notes) != 1 else ''}:"
    return head + "\n" + numbered(notes)


def numbered(notes: list) -> str:
    """'1. …', '2. …'; a note's further lines indented under it."""
    return "\n".join(f"{i}. " + "\n".join(("   " + x) if x and j else x for j, x in enumerate(n.split("\n")))
                     for i, n in enumerate(notes, 1))


def show_warnings(step: str, notes: list) -> None:
    log.warning(warning_list(step, notes), extra={"as_written": True})


class Interrupted(KeyboardInterrupt):
    """Ctrl+C, with a message saying what it cost. A KeyboardInterrupt, so the step ends `interrupted` (exit code
    130: common/common_helpers/step.py), like a Ctrl+C anywhere else; every answer already received is in the cache."""


def confirm(question: str, spent: str = "Nothing was spent.") -> None:
    """Stop until the person presses Enter (or types y or yes, in any case, spaces around it ignored); exit on
    anything else (the answers, for a person: docs/running_on_nasa_laptop.md, section 5). spent: what was paid
    for before the question.

    The gate between reading a run's summary and paying for it. Any other
    answer and a closed input (a run with nothing attached to the keyboard)
    stop the step (`stopped`); Ctrl+C interrupts it (`interrupted`), so the
    expensive path is never taken by default."""
    try:
        answer = input(f"\n{question} ")
    except EOFError:
        sys.exit(f"\nCancelled. {spent}")
    except KeyboardInterrupt:
        raise Interrupted(f"Cancelled with Ctrl+C. {spent}") from None
    if answer.strip().lower() not in ("", "y", "yes"):
        sys.exit(f"Cancelled. {spent}")
