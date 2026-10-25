# nasa_census.py — the attendance check: across ALL records, which fields are
# actually filled in, and how many distinct values do the interesting ones hold?
import json
from collections import Counter
from pathlib import Path

records = []
for f in sorted(Path("data").glob("batch_*.json")):
    records.extend(json.loads(f.read_text(encoding="utf-8")))
n = len(records)
print(f"Loaded {n} records from {len(list(Path('data').glob('batch_*.json')))} files.\n")

# --- 1. Fill rate per top-level field ---------------------------------------
filled = Counter()
seen = Counter()   # every key that appears at all, filled or not
for r in records:
    for key, val in r.items():
        seen[key] += 1
        if val not in (None, "", [], {}):
            filled[key] += 1

print(f"{len(seen)} distinct top-level fields exist across all records; "
      f"{len(filled)} are populated at least once.\n")
print("FIELD                     FILLED   % OF RECORDS")
for key in sorted(seen, key=lambda k: (-filled.get(k, 0), k)):
    cnt = filled.get(key, 0)
    print(f"{key:<25} {cnt:>7}   {100*cnt/n:5.1f}%")

# --- 2. Distinct values for the fields likely to become nodes --------------
def top(counter, k=10):
    return "\n".join(f"      {v!r}: {c}" for v, c in counter.most_common(k))

orgs = Counter(r.get("organization", {}).get("title") if r.get("organization") else None
               for r in records)
maint = Counter(r.get("maintainer") for r in records)
tags = Counter(t["name"] for r in records for t in (r.get("tags") or []))
fmts = Counter(res.get("format") for r in records for res in (r.get("resources") or []))
lic = Counter(r.get("license_title") for r in records)

print(f"\nORGANIZATIONS: {len(orgs)} distinct. Top 10:\n{top(orgs)}")
print(f"\nMAINTAINERS: {len(maint)} distinct. Top 10:\n{top(maint)}")
print(f"\nTAGS: {len(tags)} distinct, {sum(tags.values())} total uses. Top 15:\n{top(tags, 15)}")
print(f"\nFORMATS: {len(fmts)} distinct. Top 10:\n{top(fmts)}")
print(f"\nLICENSES: {len(lic)} distinct. Top 5:\n{top(lic, 5)}")

# --- 3. Notes length: is there enough text for AI enrichment later? --------
lens = sorted(len(r.get("notes") or "") for r in records)
print(f"\nNOTES length (chars): min {lens[0]}, median {lens[n//2]}, max {lens[-1]}; "
      f"empty: {sum(1 for L in lens if L == 0)}")
