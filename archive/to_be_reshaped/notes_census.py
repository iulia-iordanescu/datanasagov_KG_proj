"""
notes_census.py: let the notes field tell us what it contains.

No word list from us. Three counts and one sample, written to notes_census_report.txt:

  A. Named terms: capitalized words, acronyms, and capitalized phrases
     (AIRS, Aqua, Mars Reconnaissance Orbiter), ranked by how many notes
     mention them. Many notes = a circle worth having.
  B. The same, broken down by the 8 biggest maintainers, so a term common
     only in planetary science or only in astrophysics still shows up.
  C. For the top named terms, the words that most often sit next to them.
     "AIRS" next to "instrument" tells us its label without reading 2,000 notes.
  D. A reading sample: 5 notes from each of the 8 biggest maintainers,
     saved to notes_sample.txt, for checking by eye.
"""

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

random.seed(1)

records = []
for f in sorted(Path("data").glob("batch_*.json")):
    records.extend(json.loads(f.read_text(encoding="utf-8")))

# Words that are capitalized for grammar, not because they name something.
STOP = set("""
the this that these those a an and or of in on at to for from by with as is are was
were be been it its data dataset datasets product products level version file files
users user please note warning also each all any some more most other new
""".split())

# Tokens that look like names: Acronyms (2-10 caps/digits) or Capitalized words.
TOKEN = re.compile(r"[A-Z][A-Za-z0-9\-]*|[A-Z0-9]{2,10}")
WORD = re.compile(r"[A-Za-z][A-Za-z\-]+")


def named_terms(text):
    """Return the set of named terms in one note: single tokens and 2-3 word phrases."""
    found = set()
    for sentence in re.split(r"[.!?;:\n]+", text):
        words = sentence.split()
        for i, w in enumerate(words):
            w_clean = w.strip("(),\"'")
            is_name = (TOKEN.fullmatch(w_clean) is not None
                       and w_clean.lower() not in STOP
                       and not (i == 0 and not w_clean.isupper()))  # skip sentence-initial Capitalized
            if not is_name:
                continue
            found.add(w_clean)
            # Capitalized phrases: extend while the next words are capitalized too.
            phrase = [w_clean]
            for nxt in words[i + 1:i + 3]:
                nxt_clean = nxt.strip("(),\"'")
                if TOKEN.fullmatch(nxt_clean) and nxt_clean.lower() not in STOP:
                    phrase.append(nxt_clean)
                    found.add(" ".join(phrase))
                else:
                    break
    return found


# ---------- A + B: named terms, overall and per maintainer ----------
overall = Counter()
by_maint = defaultdict(Counter)
maint_size = Counter()
notes_by_maint = defaultdict(list)

for r in records:
    text = r.get("notes") or ""
    m = (r.get("maintainer") or "").strip() or "(none)"
    terms = named_terms(text)
    overall.update(terms)
    by_maint[m].update(terms)
    maint_size[m] += 1
    notes_by_maint[m].append((r.get("title"), text))

top_maints = [m for m, _ in maint_size.most_common(8)]

# ---------- C: context words around the top terms ----------
top_terms = [t for t, _ in overall.most_common(40)]
context = {t: Counter() for t in top_terms}
for r in records:
    text = r.get("notes") or ""
    words = text.split()
    lower = [w.strip("(),\"'").lower() for w in words]
    for i, w in enumerate(words):
        w_clean = w.strip("(),\"'")
        if w_clean in context:
            window = lower[max(0, i - 3):i] + lower[i + 1:i + 4]
            context[w_clean].update(x for x in window if WORD.fullmatch(x) and x not in STOP)

# ---------- Write the report ----------
out = []
n = len(records)
out.append(f"{n} notes scanned\n")

out.append("A. NAMED TERMS, ranked by how many notes mention them (top 80)")
out.append(f"{'term':<40} notes     %")
for t, c in overall.most_common(80):
    out.append(f"{t:<40} {c:>6}  {100*c/n:5.1f}%")

out.append("\nB. TOP 15 NAMED TERMS PER MAINTAINER (the 8 biggest)")
for m in top_maints:
    out.append(f"\n  {m}  ({maint_size[m]} records)")
    for t, c in by_maint[m].most_common(15):
        out.append(f"    {t:<36} {c:>6}")

out.append("\nC. WORDS THAT SIT NEXT TO THE TOP 40 TERMS (hints for labels)")
for t in top_terms:
    neighbors = ", ".join(f"{w} ({c})" for w, c in context[t].most_common(6))
    out.append(f"  {t:<30} {neighbors}")

Path("notes_census_report.txt").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out[:90]))
print("\n... full report in notes_census_report.txt")

# ---------- D: stratified reading sample ----------
sample = []
for m in top_maints:
    for title, text in random.sample(notes_by_maint[m], min(5, len(notes_by_maint[m]))):
        sample.append(f"=== [{m}] {title}\n{text.strip()}\n")
Path("notes_sample.txt").write_text("\n".join(sample), encoding="utf-8")
print("40 notes for reading saved to notes_sample.txt")
