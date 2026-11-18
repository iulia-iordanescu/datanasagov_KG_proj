"""
scalability · The estimates of docs/analysis/scalability.md.

Produces: outputs/analysis/scalability.json: per record and for the whole catalog, the characters sent and received,
and from them rough token counts and costs with and without prompt caching.

    py helpers/analysis/scalability.py       after prompt_sizes.py

No model call: it reads outputs/analysis/prompt_sizes.json and the six reported runs' extracted_triples.csv
(outputs/intermediate_results/060_extract/previous_runs/). Characters are measured; a token is taken as 4 characters
(060_extract/060_extract.md's own rough rule), not counted by the service. Prices: Claude Opus 5.5 list prices per
million tokens (sent 4.00, received 20.00, read from the prompt cache 0.20, written to it 5.00 US dollars; Anthropic's
published prices, platform.claude.com/docs/en/about-claude/pricing, checked 2026-11-17); what NASA's LiteLLM charges is not in the
repository.
"""
import json, statistics, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from common.files import read_csv, read_json, write_json                       # noqa: E402
HERE = ROOT / "outputs" / "analysis"                                         # the working folder (not in Git)
sizes = read_json(HERE / "prompt_sizes.json")
RUNS = {"induced schema": ["1816", "1816-2", "1816-3"], "ground truth schema": ["1817", "1817-2", "1817-3"]}
FIELDS = ("subject", "subject_class", "predicate", "object", "object_class", "source_text")
IN, OUT, READ, WRITE, CH = 4.00, 20.00, 0.20, 5.00, 4
cat = sizes["catalog"]
out = {"catalog": cat, "sample": sizes["sample"], "prices": {"input": IN, "output": OUT, "cache_read": READ, "cache_write": WRITE}}
for recipe, runs in RUNS.items():
    reqs = sizes[recipe]["requests"]
    start = reqs[0]["identical_start_chars"]
    overhead = statistics.mean(r["rest_chars"] - r["piece_chars"] for r in reqs)
    per_run = []
    for run in runs:
        answer = {r["id"]: 0 for r in reqs}; triples = {r["id"]: 0 for r in reqs}
        for row in read_csv(ROOT / "outputs/intermediate_results/060_extract/previous_runs" / f"060_extract_2026-11-05_{run}" / "extracted_triples.csv"):
            answer[row["id"]] += len(json.dumps({k: row[k] for k in FIELDS}, ensure_ascii=False)) + 2
            triples[row["id"]] += 1
        per_run.append({"run": run, "answer_chars": answer, "triples": triples})
    a = [statistics.mean(p["answer_chars"][i] for p in per_run) for i in per_run[0]["answer_chars"]]
    t = [statistics.mean(p["triples"][i] for p in per_run) for i in per_run[0]["triples"]]
    prompt = [r["prompt_chars"] for r in reqs]
    s = {"identical_start_chars": start, "schema_text_chars": sizes[recipe]["schema_text_chars"], "overhead_chars_after_start": overhead,
         "sample_prompt_chars": {"mean": statistics.mean(prompt), "min": min(prompt), "max": max(prompt)},
         "sample_answer_chars": {"mean": statistics.mean(a), "min": min(a), "max": max(a)},
         "sample_triples": {"mean": statistics.mean(t), "min": min(t), "max": max(t)},
         "sample_tokens_est": {"input_mean": statistics.mean(prompt) / CH, "input_min": min(prompt) / CH, "input_max": max(prompt) / CH,
                               "output_visible_mean": statistics.mean(a) / CH, "output_visible_min": min(a) / CH, "output_visible_max": max(a) / CH}}
    def cost(start_price_tokens, rest_tok, out_tok): return start_price_tokens + rest_tok * IN / 1e6 + out_tok * OUT / 1e6
    start_tok = start / CH
    s["sample_cost_est_per_record"] = {
        "no_cache": {"mean": statistics.mean(cost(start_tok * IN / 1e6, (p - start) / CH, x / CH) for p, x in zip(prompt, a)),
                     "min": min(cost(start_tok * IN / 1e6, (p - start) / CH, x / CH) for p, x in zip(prompt, a)),
                     "max": max(cost(start_tok * IN / 1e6, (p - start) / CH, x / CH) for p, x in zip(prompt, a))},
        "start_read_from_cache": {"mean": statistics.mean(cost(start_tok * READ / 1e6, (p - start) / CH, x / CH) for p, x in zip(prompt, a)),
                                  "min": min(cost(start_tok * READ / 1e6, (p - start) / CH, x / CH) for p, x in zip(prompt, a)),
                                  "max": max(cost(start_tok * READ / 1e6, (p - start) / CH, x / CH) for p, x in zip(prompt, a))}}
    n = cat["requests"]
    rest_tok = (overhead * n + cat["piece_chars_total"]) / CH
    out_tok = statistics.mean(a) / CH * cat["records"]
    out_tok_scaled = out_tok * cat["piece_chars_mean_per_record"] / sizes["sample"]["piece_chars_mean_per_record"]
    s["catalog_est"] = {"requests": n, "input_tokens_start": start_tok * n, "input_tokens_rest": rest_tok, "output_visible_tokens": out_tok,
                        "output_visible_tokens_scaled_by_text_length": out_tok_scaled,
                        "cost_no_cache": start_tok * n * IN / 1e6 + rest_tok * IN / 1e6 + out_tok * OUT / 1e6,
                        "cost_all_reads_but_one_write": (start_tok * WRITE + start_tok * (n - 1) * READ) / 1e6 + rest_tok * IN / 1e6 + out_tok * OUT / 1e6,
                        "cost_half_reads_half_writes": (start_tok * n / 2 * WRITE + start_tok * n / 2 * READ) / 1e6 + rest_tok * IN / 1e6 + out_tok * OUT / 1e6,
                        "cost_input_start_no_cache": start_tok * n * IN / 1e6, "cost_input_start_all_read": start_tok * n * READ / 1e6,
                        "cost_input_rest": rest_tok * IN / 1e6, "cost_output_visible": out_tok * OUT / 1e6,
                        "cost_output_visible_scaled": out_tok_scaled * OUT / 1e6}
    out[recipe] = s
write_json(HERE / "scalability.json", out)
print("wrote outputs/analysis/scalability.json")
