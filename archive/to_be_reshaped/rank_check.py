# This file counts records per maintainer, and displays them ranked. 
# Maintainer names that differ in case, punctuation, word order, or titles (Dr., Ph.D)
# are treated as the same maintainer and become joined into a single group under one common name
# in "John Doe" format. Maintainer names that differ by a middle name
# or initial, e.g. "Lola Olsen" and "Lola M. Olsen" stay apart. 

# A joined group is printed in "John Doe" format; a maintainer with a single
# spelling is printed exactly as it appears in the data, untouched.
# The joined groups are printed at the end of the printed maintainer rankings.
#
import json, re, collections

TITLES = {"dr", "mr", "ms", "mrs", "phd", "ph", "d", "jr", "sr", "prof"}

def key(name):
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower())
             if w not in TITLES]
    return " ".join(sorted(words))          # sorted: handles swapped names

def display(spellings):
    """The name for a group whose spellings were JOINED, as "John Doe":
    titles dropped, and SHOUTED names title-cased. A spelling that is
    already mixed case is preferred and left alone, so acronyms such as
    NASA survive. A maintainer with only one spelling is never touched."""
    ranked = spellings.most_common()
    name = next((n for n, _ in ranked if not n.isupper()), ranked[0][0])
    words = [w for w in re.split(r"[\s,]+", name.strip())
             if re.sub(r"[^a-z0-9]", "", w.lower()) not in TITLES and w]
    name = " ".join(words).strip(" ,.")
    return name.title() if name.isupper() else name


groups = collections.defaultdict(collections.Counter)
for r in json.load(open("inputs.json", encoding="utf-8")):
    groups[key(r["group"])][r["group"]] += 1

merged = []
for rank, (k, spellings) in enumerate(sorted(
        groups.items(), key=lambda kv: -sum(kv[1].values())), 1):
    name = (display(spellings) if len(spellings) > 1
            else spellings.most_common(1)[0][0])
    print(f"{rank:>3}  {name:<45} {sum(spellings.values())}")
    if len(spellings) > 1:
        merged.append(f"{name}: {' || '.join(sorted(spellings))}")

for line in merged:
    print(f"\nJoined:\n{line}")