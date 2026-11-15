"""
prompt_sizes · The size, in characters, of each request step 060 sent in the six reported runs, with nothing sent.

Produces: outputs/analysis/prompt_sizes.json: per recipe, the schema's characters and each request's characters (the
whole prompt, its start that is identical in every request, the record's text); and for the whole catalog, the number
of requests and the characters of text.

    py helpers/analysis/prompt_sizes.py [commit]      default 7e81bae

The prompt changed after the six runs, so the script takes the code and prompts of the commit whose prompt files have
the sha256 the six runs' manifests record (git archive, into a temporary folder outside the repository, removed at the end) and builds each
record's prompt with that commit's own functions (060_extract_helpers/extract.py, ask_model's prompt_for). No model
call (llm.forbid_model_calls). Reads 020's records.jsonl, 030's splits.json, 040's the_schema.json, the ground truth
files and the six runs' extracted_triples_details.json.
"""
import importlib.util, io, statistics, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORK = REPO / "outputs" / "analysis"                                        # the working folder (not in Git)
COMMIT = sys.argv[1] if len(sys.argv) > 1 else "7e81bae"
HERE = Path(tempfile.mkdtemp(prefix=f"code_at_{COMMIT}_"))                    # outside the repository: no test sweeps it
archive = subprocess.run(["git", "archive", COMMIT, "060_extract", "common", "annotations/ground_truth_schema.txt",
                          "annotations/schema_additions.txt"], cwd=REPO, capture_output=True, check=True).stdout
tarfile.open(fileobj=io.BytesIO(archive)).extractall(HERE)
sys.path.insert(0, str(HERE))
from common import extraction, llm                                              # noqa: E402  (that commit's code)
from common.chunking import pieces                                              # noqa: E402
from common.files import read_json, read_jsonl, write_json                     # noqa: E402
llm.forbid_model_calls("py helpers/analysis/prompt_sizes.py is free: it builds prompts and sends nothing")

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod); return mod

sys.path.insert(0, str(HERE / "060_extract" / "060_extract_helpers"))
schema_stage = load("schema", HERE / "060_extract/060_extract_helpers/schema.py")
extract = load("extract", HERE / "060_extract/060_extract_helpers/extract.py")
RES = REPO / "outputs/intermediate_results"
records = {}
for _, r in read_jsonl(RES / "020_clean/records.jsonl"):
    records[r["id"]] = r
out = {}
for recipe, schema_path, run in (("induced schema", RES / "040_induce_schema/the_schema.json", "060_extract_2026-11-05_1816"),
                                 ("ground truth schema", HERE / "annotations/ground_truth_schema.txt", "060_extract_2026-11-05_1817")):
    inputs = {"schema": schema_path, "additions": HERE / "annotations/schema_additions.txt",
              "splits": RES / "030_split/splits.json", "ground_truth": REPO / "annotations/ground_truth/batch_*.csv",
              "records": RES / "020_clean/records.jsonl"}
    schema = schema_stage.load_schema(inputs)
    details = read_json(REPO / "outputs/intermediate_results/060_extract/previous_runs" / run / "extracted_triples_details.json")
    rows = []
    for d in details["records"]:
        rec = records[d["id"]]
        ps = pieces(rec, 8000)
        for piece in ps:
            prompt = extraction.prompt(extract.PROMPT, schema.text, rec, piece, **extraction.task_parts(extraction.SCOPE_SCHEMA))
            start = prompt.index(extraction.BEGIN_LINE)
            rows.append({"id": d["id"], "pieces": len(ps), "prompt_chars": len(prompt), "identical_start_chars": start,
                         "rest_chars": len(prompt) - start, "piece_chars": len(piece)})
    out[recipe] = {"schema_text_chars": len(schema.text), "requests": rows}
    print(recipe, "schema chars", len(schema.text), "requests", len(rows),
          "identical start", sorted({r["identical_start_chars"] for r in rows}),
          "rest mean", statistics.mean(r["rest_chars"] for r in rows), min(r["rest_chars"] for r in rows), max(r["rest_chars"] for r in rows))
# the whole catalog: pieces per record and characters of text, with the same splitter
n_pieces, chars = [], []
for r in records.values():
    ps = pieces(r, 8000)
    n_pieces.append(len(ps)); chars.append(sum(len(p) for p in ps))
out["catalog"] = {"records": len(records), "requests": sum(n_pieces), "records_with_more_than_one_piece": sum(1 for n in n_pieces if n > 1),
                  "records_with_no_piece": sum(1 for n in n_pieces if n == 0),
                  "piece_chars_total": sum(chars), "piece_chars_mean_per_record": statistics.mean(chars), "piece_chars_median_per_record": statistics.median(chars),
                  "piece_chars_max_per_record": max(chars)}
sample = [sum(len(p) for p in pieces(records[x["id"]], 8000)) for x in details["records"]]
out["sample"] = {"records": len(sample), "piece_chars_mean_per_record": statistics.mean(sample), "piece_chars_median_per_record": statistics.median(sample),
                 "piece_chars_min": min(sample), "piece_chars_max": max(sample)}
print(out["catalog"]); print(out["sample"])
write_json(WORK / "prompt_sizes.json", out)
shutil.rmtree(HERE, ignore_errors=True)
