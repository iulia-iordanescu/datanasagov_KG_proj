"""
induction_trace.py -- what step 040 did with the triple instances that match
a regular expression, read from its output files. Read-only, no model call.

    py helpers/audit.py --induction "aboard|on board"

For each triple instance in induction_evidence.json whose predicate instance,
source text, predicate label or final predicate matches (case ignored): its
record, the triple instance, the label stage 3 gave its predicate instance,
its spelling fold and the label stage 4 merged that into (both stage 4), the
split of stage 5 its subject's or object's entity class or its pattern put it
in, if any, and the predicate stage 5's merging again made of it (so the final
predicate), and whether that predicate is in the_schema.json or
deferred (with the reason), with its support. Unverified triple instances
that match are shown too: they got no label and count toward nothing. Then a
summary: the matched triple instances per final predicate.

Stage 4 records each merge with the label at the END of its chain (merge.py
follows chains before writing), so a chain A -> B -> C shows as A -> C.
Stage 4 folds spellings before merging (since 2026-11-15); an evidence file of
an earlier run folded them after merging, so the chain applies a fold again
after the merge, which changes nothing for a later run. An evidence file of a
run before 2026-11-15 splits by the object's entity class only ("into":
{predicate: {object class: new predicate}}) and has no merging again; the chain
reads it as that run did (only the object's entity class needed a label).
"""
from __future__ import annotations

import collections
import json
import re
from pathlib import Path

from common.files import read_json
from common.step import RESULTS_DIR, repo_path

STEP = "040_induce_schema"
SCHEMA_NAME = "the_schema.json"
EVIDENCE_NAME = "induction_evidence.json"
SOURCE_SHOWN = 220                  # characters of a source text shown
NO_LABEL = "(no label)"
UNVERIFIED = "(unverified)"


def _short(text: str, n: int = SOURCE_SHOWN) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n - 1] + "…"


def _read(folder: Path, name: str):
    path = folder / name
    if not path.exists():
        raise FileNotFoundError(
            f"{repo_path(path)} doesn't exist, so there is nothing to trace. It is written by step 040: run "
            f"`py 040_induce_schema/run.py` (or point --folder at a folder that holds {SCHEMA_NAME} and "
            f"{EVIDENCE_NAME}, e.g. one under previous_runs/).")
    try:
        return read_json(path)
    except json.JSONDecodeError as e:
        raise ValueError(f"{repo_path(path)} isn't valid JSON ({e}): it may be cut short. Run "
                         f"`py 040_induce_schema/run.py` again to rewrite it.") from None


def _status(schema: dict, evidence: dict) -> dict:
    """{final predicate: (status, support, maintainers)} for every predicate found."""
    out = {}
    for p in evidence.get("counts", {}).get("predicates", []):
        out[p["component_class"]] = ["found, but neither in the schema nor deferred", p.get("support"), len(p.get("maintainers", []))]
    for d in schema.get("deferred", []):
        if d.get("entry_type") == "predicate":
            row = out.setdefault(d["schema_entry"], ["", d.get("support"), None])
            row[0] = f"DEFERRED ({d.get('reason', 'no reason recorded')})"
    for p in schema.get("predicates", []):
        row = out.setdefault(p["component_class"], ["", p.get("support"), len(p.get("maintainers", []))])
        row[0] = "IN THE SCHEMA"
    return {k: tuple(v) for k, v in out.items()}


def _why_unlabeled(evidence: dict, instance: str) -> str:
    for r in evidence.get("refused", {}).get("labels", {}).get("predicate", []):
        if r.get("component_instance") == instance:
            return f"the service refused to label it ({r.get('why', '')})"
    if instance in evidence.get("unlabeled", {}).get("predicate", []):
        return "the model left it unlabeled, even asked twice"
    return "not in `labels` (was 040 run with this text?)"


def trace_induction(pattern: str, limit: int = 30, folder: Path | None = None, out=print) -> int:
    """Prints the trace; returns the number of triple instances that matched."""
    folder = Path(folder) if folder else RESULTS_DIR / STEP
    schema, evidence = _read(folder, SCHEMA_NAME), _read(folder, EVIDENCE_NAME)
    rx = re.compile(pattern, re.IGNORECASE)

    labels = evidence.get("labels", {}).get("predicate", {})
    merged = {m["label"]: m["into"] for m in evidence.get("merges", []) if m.get("kind") == "predicate"}
    folded = {s: f["into"] for f in evidence.get("spelling_folds", []) if f.get("kind") == "predicate"
              for s in f.get("folded", []) if s != f["into"]}
    status = _status(schema, evidence)

    entity_labels = evidence.get("labels", {}).get("entity", {})
    entity_merged = {m["label"]: m["into"] for m in evidence.get("merges", []) if m.get("kind") == "entity class"}
    entity_folded = {s: f["into"] for f in evidence.get("spelling_folds", []) if f.get("kind") == "entity class"
                     for s in f.get("folded", []) if s != f["into"]}
    split_into = evidence.get("splits", {}).get("into", {})
    merged_again = evidence.get("splits", {}).get("final", {})

    def entity_class(instance: str):
        """A subject or object instance's final entity class (stage 3's label, folded, merged, folded), or None."""
        c = entity_labels.get(instance)
        c = entity_folded.get(c, c)
        c = entity_merged.get(c, c)
        return entity_folded.get(c, c)

    def split_of(final: str, subj: str, obj: str) -> tuple:
        """(new predicate, the words for how it was reached), or (None, None): stage 5's split of the predicate."""
        spec = split_into.get(final)
        if not isinstance(spec, dict) or not spec:
            return None, None
        sc, oc = entity_class(subj), entity_class(obj)
        if "by" not in spec:                    # an earlier run's evidence: by the object's entity class only
            return spec.get(oc), f"its object's entity class, {oc}"
        if not (sc and oc):
            return None, None
        by = spec["by"]
        group = sc if by == "subject" else oc if by == "object" else f"{sc} -> {oc}"
        return spec.get("to", {}).get(group), f"its {by}'s entity class, {group}" if by != "pattern" else             f"its pattern, {group}"

    def chain(words: str, obj: str = "", subj: str = "") -> tuple:
        """(final predicate, the chain as text)."""
        label = labels.get(words)
        if label is None:
            return NO_LABEL, f"no label: {_why_unlabeled(evidence, words)}"
        steps, final = [f"label {label}"], label
        if final in folded:
            final = folded[final]
            steps.append(f"spelling fold to {final} (stage 4)")
        if final in merged:
            final = merged[final]
            steps.append(f"merged into {final} (stage 4)")
        if final in folded:                     # an earlier run's evidence: folded after merging
            final = folded[final]
            steps.append(f"spelling fold to {final} (stage 4)")
        new, how = split_of(final, subj, obj)
        if new:
            final = new
            steps.append(f"split to {final} by {how} (stage 5)")
        again = merged_again.get(final, final)
        if again != final:
            final = again
            steps.append(f"merged again into {final} (stage 5)")
        return final, " -> ".join(steps)

    hits = []                                   # (record id, triple instance, verified?, final, chain)
    for t in evidence.get("texts", []):
        for verified, key in ((True, "triple_instances"), (False, "unverified")):
            for ti in t.get(key, []):
                words = ti.get("predicate", "")
                final, how = chain(words, ti.get("object", ""), ti.get("subject", "")) if verified else (UNVERIFIED, "")
                looked_in = [words, ti.get("source_text", "")] + ([labels.get(words) or "", final] if verified else [])
                if any(rx.search(x or "") for x in looked_in):
                    hits.append((t.get("id", "?"), ti, verified, final, how))

    made = evidence.get("made", {})
    out(f"Step 040 run {made.get('run_id', 'unknown')} ({repo_path(folder)}): {len(evidence.get('texts', []))} texts. "
        f"{len(hits)} triple instance(s) match /{pattern}/ (in the predicate instance, source text, label or "
        f"final predicate; case ignored).")
    if not hits:
        out("Nothing matches: no text of this run states it in a way the regular expression catches. Try a wider "
            "one (other words for the relationship), or check the record ids with `py helpers/audit.py <record id>`.")
        return 0
    out("")
    for rid, ti, verified, final, how in hits[:limit]:
        out(f"{rid}  \"{ti.get('subject', '')}\" -- \"{ti.get('predicate', '')}\" -- \"{ti.get('object', '')}\"")
        out(f"    source text: \"{_short(ti.get('source_text', ''))}\"")
        if not verified:
            out(f"    UNVERIFIED ({', '.join(map(str, ti.get('errors', []))) or 'no reason recorded'}): left out "
                f"before labeling, so it counts toward no predicate")
            continue
        if final == NO_LABEL:
            out(f"    {how}: counts toward no predicate")
            continue
        state, support, maint = status.get(final, ("NOT FOUND in the counts", None, None))
        backing = f"; support {support}" + (f", {maint} maintainer(s)" if maint is not None else "") \
            if support is not None else ""
        out(f"    {how} = {final}: {state}{backing}")
    if len(hits) > limit:
        out(f"... {len(hits) - limit} more triple instance(s) not shown (--limit {len(hits)} shows all)")

    out("")
    out("Summary: matched triple instances per final predicate")
    per = collections.Counter(final for _, _, _, final, _ in hits)
    words = collections.defaultdict(collections.Counter)
    for _, ti, _, final, _ in hits:
        words[final][ti.get("predicate", "")] += 1
    rows = per.most_common()
    for final, n in rows[:limit]:
        state, support, _ = status.get(final, ("", None, None))
        if final == UNVERIFIED:
            state = "left out, counts toward nothing"
        elif final == NO_LABEL:
            state = "counts toward no predicate"
        shown = ", ".join(f"\"{w}\"" for w, _ in words[final].most_common(3))
        out(f"  {n:4d}  {final}: {state}" + (f", support {support}" if support is not None else "")
            + f"  e.g. {shown}")
    if len(rows) > limit:
        out(f"  ... {len(rows) - limit} more predicate(s) not shown")
    return len(hits)
