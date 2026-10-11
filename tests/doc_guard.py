"""
tests/doc_guard.py -- proves that the docs changed only as agreed.

Every agreed edit to a doc is recorded in a ledger (file, old text, new text),
kept in .git/doc_guard_ledger.json: never committed, never published. The
check then takes each changed doc as of the last commit, applies the recorded
edits to its text, and compares the result with the doc as it is now. Both are
compared as plain text (links reduced to their words), because the link fixer
may add or remove link markup on its own. Anything no recorded edit explains,
added, deleted or changed, fails the check, which prints it. A link that is
gone from the doc while its words remain fails too: the link fixer only
removes duplicate links, never a link's last copy.

    from doc_guard import edit
    edit("070_evaluate/metrics/pairs.md", "old words", "new words")   # does it and records it

    py tests/doc_guard.py check      # every changed doc against the ledger
    py tests/doc_guard.py clear      # after a commit: start a new ledger

A doc is any tracked *.md file outside to_be_reshaped/. Standard library only.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / ".git" / "doc_guard_ledger.json"
LINK = re.compile(r"\[([^\[\]\n]*)\]\(([^)\n]*)\)")


def term(t: str) -> str:
    """A linked term's singular, lowercased: "classes" -> "class", "triples" -> "triple", "class" stays."""
    t = re.sub(r"[*`]", "", t).lower()
    if t.endswith(("sses", "xes", "ches", "shes")):
        return t[:-2]
    return t[:-1] if t.endswith("s") and not t.endswith("ss") else t


def plain(text: str) -> str:
    """The text with every link reduced to its words."""
    return LINK.sub(r"\1", text)


def outside_links(text: str) -> str:
    """The text with every link left out: a term whose words occur only inside another link (model, in a link of
    model calls) isn't left unlinked."""
    return LINK.sub(" ", text)


def _ledger() -> list:
    return json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else []


def _record(rel: str, old: str, new: str, count: int) -> None:
    entries = _ledger()
    entries.append({"file": rel, "old": old, "new": new, "count": count})
    LEDGER.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")


def edit(rel: str, old: str, new: str, count: int = 1) -> None:
    """Replace `old` by `new` in the doc `rel` (`count` times, asserted), matching the doc's plain text, and
    record it. A line whose matched text holds a link keeps every link whose words survive the edit."""
    path = ROOT / rel
    lines = path.read_text(encoding="utf-8").split("\n")
    hits = [(n, plain(l).count(old)) for n, l in enumerate(lines) if old in plain(l)]
    assert sum(c for _, c in hits) == count, (rel, old[:80], hits)
    for n, _ in hits:
        if old in lines[n]:
            lines[n] = lines[n].replace(old, new)
            continue
        links = LINK.findall(lines[n])
        line = plain(lines[n]).replace(old, new)
        for text, url in links:                        # put back each link whose words are still there, first use
            # only an existing link is off limits: a link's words may sit inside **bold** or be `code` themselves
            protect = [m.span() for m in LINK.finditer(line)]
            for m in re.finditer(r"(?<![\w\[])" + re.escape(text) + r"(?![\w\]])", line):
                if not any(a <= m.start() < b for a, b in protect):
                    line = line[:m.start()] + f"[{text}]({url})" + line[m.end():]
                    break
        lines[n] = line
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    _record(rel, old, new, count)


def edit_block(rel: str, old: str, new: str) -> None:
    """Replace the exact text `old` (whole lines, links and all, found once) by `new`, and record it. For moving and
    regrouping whole lines: they keep their links because they are copied as they are."""
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, (rel, old[:80], text.count(old))
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    _record(rel, plain(old), new, 1)


def create(rel: str, text: str) -> None:
    """Write a new doc `rel` (it must not exist yet), and record it."""
    path = ROOT / rel
    assert not path.exists(), rel
    path.write_text(text, encoding="utf-8", newline="\n")
    entries = _ledger()
    entries.append({"file": rel, "old": "", "new": text, "count": 1, "create": True})
    LEDGER.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")


def _docs_changed() -> list:
    out = subprocess.run(["git", "diff", "--name-only", "HEAD", "--", "*.md"], cwd=ROOT, capture_output=True,
                         text=True, encoding="utf-8").stdout.split()
    new = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", "*.md"], cwd=ROOT,
                         capture_output=True, text=True, encoding="utf-8").stdout.split()
    return [f for f in out + new if not f.startswith("to_be_reshaped/")]


def _at_head(rel: str) -> str:
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else ""


def check() -> bool:
    """True when every changed doc is its last committed version plus the recorded edits (plain text)."""
    entries = _ledger()
    ok = True
    for rel in _docs_changed():
        before, now = _at_head(rel), (ROOT / rel).read_text(encoding="utf-8")
        expected = plain(before)
        for e in (e for e in entries if e["file"] == rel):
            if e.get("create"):
                if before:                       # "created" over a committed doc: never explained
                    print(f"FAIL {rel}: recorded as a new doc, but it was already committed")
                    ok = False
                expected = plain(e["new"])       # a new doc: all of it, as written
                continue
            if expected.count(e["old"]) < 1:
                print(f"FAIL {rel}: a recorded edit no longer applies: {e['old'][:100]!r}")
                ok = False
                continue
            expected = expected.replace(e["old"], plain(e["new"]))   # an edit may bring a link: compared as its words
        if expected != plain(now):
            ok = False
            print(f"FAIL {rel}: changes no recorded edit explains:")
            a, b = expected.split("\n"), plain(now).split("\n")
            import difflib
            for d in difflib.unified_diff(a, b, "expected", "actual", lineterm="", n=0):
                if not d.startswith(("---", "+++", "@@")):
                    print("   ", d[:300])
        lost = sorted(set(LINK.findall(before)) - set(LINK.findall(now)))
        gained = sorted(set(LINK.findall(now)) - set(LINK.findall(before)))
        words_now = outside_links(now)
        terms_now = {term(t) for t, _ in LINK.findall(now)}
        # a link counts as lost when its words remain but nothing links that term (singular or plural) any more:
        # the link fixer only removes duplicates, never a term's last link; a web link counts by its address
        lost_kept = [t for t, u in lost if re.search(r"(?<![\w])" + re.escape(t) + r"(?![\w])", words_now)
                     and (all(u != u2 for _, u2 in LINK.findall(now)) if u.startswith("http") else term(t) not in terms_now)]
        if lost_kept:
            ok = False
            print(f"FAIL {rel}: links gone whose words remain: {lost_kept}")
        if gained:
            print(f"     {rel}: {len(gained)} link(s) added")
    print("OK: every doc change is a recorded edit" if ok else "NOT OK")
    return ok


def history() -> list:
    """Every link any commit dropped while its words stayed, and that is still missing: [(commit, doc, text, url)].
    A web link counts as missing when its address is nowhere in the doc now; another link counts as missing when
    nothing in the doc links the same term (any target, singular or plural) now. Words that a later edit removed,
    and links into docs or anchors that were split or renumbered on purpose, show up too: read each before acting."""
    def git(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                              errors="replace").stdout

    found, seen = [], set()
    for c in git("log", "--format=%H", "--reverse", "--", "*.md").split():
        for rel in git("diff-tree", "--no-commit-id", "--name-only", "-r", c, "--", "*.md").split():
            if rel.startswith("to_be_reshaped/") or not (ROOT / rel).exists():
                continue
            before, after = git("show", f"{c}^:{rel}"), git("show", f"{c}:{rel}")
            if not before or not after:
                continue
            now = (ROOT / rel).read_text(encoding="utf-8")
            links_now, words_now = LINK.findall(now), outside_links(now)
            for text, url in set(LINK.findall(before)) - set(LINK.findall(after)):
                if (rel, text, url) in seen:
                    continue
                seen.add((rel, text, url))
                words = re.sub(r"[*`]", "", text)
                if not re.search(r"(?<![\w])" + re.escape(words) + r"(?![\w])", words_now, re.I):
                    continue
                if url.startswith("http"):
                    missing = all(u != url for _, u in links_now)
                else:
                    missing = all(term(t) != term(text) for t, _ in links_now)
                if missing:
                    found.append((c[:7], rel, text, url))
    return found


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "check"
    if what == "history":
        reviewed_file = ROOT / "tests" / "doc_guard_reviewed.txt"
        reviewed = {tuple(l.split("\t")[:3]) for l in reviewed_file.read_text(encoding="utf-8").split("\n")
                    if l and not l.startswith("#")} if reviewed_file.exists() else set()
        new = [(c, rel, text, url) for c, rel, text, url in history() if (c, rel, f"[{text}]({url})") not in reviewed]
        for c, rel, text, url in new:
            print(f"{c}  {rel}: [{text}]({url})")
        print(f"{len(new)} dropped link(s) not reviewed yet (reviewed ones: tests/doc_guard_reviewed.txt)")
        sys.exit(1 if new else 0)
    if what == "clear":
        LEDGER.unlink(missing_ok=True)
        print("ledger cleared")
    else:
        sys.exit(0 if check() else 1)
