"""
common/common_helpers/model_rules.py -- builds the model's copy of the rules from the annotation guidelines.

The rules a model follows when it extracts triple instances (step 040), drafts (step 050) and extracts (step 060)
are the rules a person follows when writing the ground truth, so that step 070 never counts the model wrong for
following a rule the ground truth does not follow. The rules have one home, annotations/guidelines.md (its sections
RULE_SECTIONS); the model's copy, common/common_prompts/extraction_rules.txt (MODEL_COPY), is generated from it and
never edited by hand. Every way in which the model's copy differs is listed, with its reason, in one file,
annotations/rules_model_differences.txt (DIFFERENCES), so a difference that isn't listed there can't exist.

    from common.model_rules import build, write_model_copy
    build()                  # the model's copy as text (ValueError, saying what to fix, on a bad entry)
    write_model_copy()       # writes MODEL_COPY when its content changes; True if it did

HOW THE COPY IS BUILT. Each paragraph and bullet of RULE_SECTIONS becomes plain text: links reduced to their words,
** * and ` taken out (the inside of a code span is kept as written). Every *Suppose:* … *Then:* … bullet (an example
built from a ground truth record, which no prompt may quote: tests/test_docs.py, PromptsQuoteNoGroundTruth) is left
out. Then, in this order:
  1. "$" becomes "$$", for Python's string.Template (prompt_files.fill).
  2. Each `replace` entry of DIFFERENCES replaces its guidelines words, found exactly once, with the model's words
     (none, for words that are only the person's). A bullet left with no words is dropped.
  3. Each ground truth schema name in parentheses is taken out: the rules state each fact by its meaning, with the
     ground truth schema's predicate or entity class after it in parentheses ("collected by the instrument
     (ACQUIRED_BY_INSTRUMENT)"), and the model uses the schema its task names (040 none, 050 the ground truth
     schema, 060 the current schema).
  4. Each `map` entry replaces a word everywhere ("ground truth triple" -> "triple").
  5. The `examples` entries (invented examples) go after the rule or part they name, the `preamble` before the
     rules, and the `also` items in a section ALSO after them.
The build fails, naming the entry, when a replace entry's words aren't found exactly once, an examples entry names
no rule or part, an entry other than examples has no reason, or the result still holds words that are only the
person's ("ground truth", "annotations/", a schema predicate name, "Suppose:").
Standard library only (and common.schema_io for the ground truth schema's names).
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

from common.files import read_text, write_text

ROOT = Path(__file__).resolve().parents[2]
GUIDELINES = ROOT / "annotations" / "guidelines.md"
DIFFERENCES = ROOT / "annotations" / "rules_model_differences.txt"
MODEL_COPY = ROOT / "common" / "common_prompts" / "extraction_rules.txt"
SCHEMA = ROOT / "annotations" / "ground_truth_schema.txt"
COMMAND = "py helpers/build_rules.py"
#: The sections of the guidelines that hold the rules and the words they use, in their order.
RULE_SECTIONS = ("How the rules use their words", "What counts as a fact", "Writing a classed triple")
KINDS = ("preamble", "replace", "map", "examples", "also")
WIDTH = 76
#: Words that only the person's copy may hold; the build fails if the model's copy still has one.
PERSON_ONLY = ("ground truth", "annotations/", "Suppose:", "Then:", "step 0", ".md", ".csv")
LINK = re.compile(r"\[([^\[\]\n]*)\]\(([^)\n]*)\)")
NBSP = " "


def plain(md: str) -> str:
    """Markdown as plain text: links reduced to their words, ** * ` taken out, the inside of `code` kept."""
    spans = []

    def keep(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"
    text = re.sub(r"`([^`]+)`", keep, md)
    text = LINK.sub(r"\1", text).replace("**", "").replace("*", "")
    text = re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], text)
    return " ".join(text.split())


def _items(guidelines: str) -> list:
    """[{"section", "level", "text", "rule", "part", "example"}]: each paragraph and bullet of RULE_SECTIONS, in order.
    level: 0 a rule's first line or a paragraph, 1 a bullet under it, 2 a bullet under that; a bullet of the words
    section is level 1. "part" is the bold title of the bullet the item is or is under ("" for none)."""
    items, section, rule, part, cur = [], None, None, "", None
    for line in guidelines.split("\n"):
        h = re.match(r"^(#{2,3}) (.+)", line)
        if h:
            section = h.group(2).strip() if h.group(1) == "##" and h.group(2).strip() in RULE_SECTIONS else None
            rule, part, cur = None, "", None
            if section:
                items.append({"section": section, "level": -1, "text": section, "rule": None, "part": "",
                              "example": False})
            continue
        if section is None or not line.strip():
            continue
        r = re.match(r"^(\d+)\. (.*)", line)
        b = re.match(r"^( *)- (.*)", line)
        if r:
            rule, part = int(r.group(1)), ""
            cur = {"section": section, "level": 0, "text": r.group(2), "rule": rule, "part": "", "example": False}
        elif b:
            depth = 1 if rule is None else max(1, len(b.group(1)) // 4)    # a bullet of the words section: 1
            body = b.group(2)
            example = body.startswith("*Suppose:*")
            title = re.match(r"^\*\*(.+?)\*\*", body)
            if not example and depth == 1:
                part = plain(title.group(1)).rstrip(".") if title else ""
            cur = {"section": section, "level": depth, "text": body, "rule": rule,
                   "part": part if depth >= 1 else "", "example": example}
        elif line.startswith(" ") and cur:
            cur["text"] += " " + line.strip()
            continue
        else:
            cur = {"section": section, "level": 0, "text": line, "rule": None, "part": "", "example": False}
        items.append(cur)
    return items


def read_differences(text: str) -> list:
    """[{"kind", "where", "reason", "body": [lines], "line"}]: the entries of DIFFERENCES."""
    entries, cur = [], None
    for n, line in enumerate(text.split("\n"), 1):
        if line.startswith("@@ "):
            parts = [p.strip() for p in line[3:].split("|")]
            parts += [""] * (3 - len(parts))
            if len(parts) != 3 or parts[0] not in KINDS:
                raise ValueError(f"{DIFFERENCES.name}:{n}: an entry starts \"@@ kind | where | reason\" (an examples entry needs no reason), kind one of "
                                 f"{', '.join(KINDS)}: \"{line}\"")
            cur = {"kind": parts[0], "where": parts[1], "reason": parts[2], "body": [], "line": n}
            entries.append(cur)
        elif cur is not None:
            cur["body"].append(line)
        elif line.strip() and not line.startswith("#"):
            raise ValueError(f"{DIFFERENCES.name}:{n}: a line before the first entry must start with \"#\"")
    for e in entries:
        while e["body"] and not e["body"][-1].strip():
            e["body"].pop()
        if e["kind"] != "examples" and not e["reason"]:
            raise ValueError(f"{DIFFERENCES.name}:{e['line']}: this {e['kind']} entry needs its reason")
    return entries


def _bullets(body: list) -> list:
    """The "- " items of an entry's body, each with its indented continuation lines joined."""
    out = []
    for line in body:
        if line.startswith("- "):
            out.append(line[2:].strip())
        elif line.strip():
            if not out:
                raise ValueError(f"a line that is neither a \"- \" item nor its indented continuation: \"{line}\"")
            out[-1] += " " + line.strip()
    return out


def _schema_names(path: Path = SCHEMA) -> list:
    from common.schema_io import read_ground_truth_schema
    s = read_ground_truth_schema(path)
    return sorted(set(s["entity_classes"]) | set(s["predicates"]), key=len, reverse=True)


def strip_schema_names(text: str, names: list) -> str:
    """The text without the schema names in parentheses: " (NAME)" and " (NAME, NAME)" go, and so does ", NAME"
    inside parentheses ("(each file's period, HAS_GRANULE_DURATION; …)")."""
    n = "(?:" + "|".join(re.escape(x) for x in names) + ")"
    text = re.sub(rf" ?\({n}(?:, {n})*\)", "", text)
    text = re.sub(rf", {n}(?=[;,)])", "", text)
    return re.sub(rf"\({n}, ", "(", text)


def _wrap(text: str, first: str, rest: str) -> list:
    # a list number inside a rule ("1. ", "2. ") is kept off the start of a line, where it would read as a rule
    text = re.sub(r"(?<=\s)(\d+)\. ", lambda m: f"{m.group(1)}.{NBSP}", " " + text)[1:]
    lines = textwrap.wrap(text, width=WIDTH, initial_indent=first, subsequent_indent=rest,
                          break_long_words=False, break_on_hyphens=False)
    return [l.replace(NBSP, " ") for l in lines]


def build(guidelines_path: Path = GUIDELINES, differences_path: Path = DIFFERENCES, schema_path: Path = SCHEMA) -> str:
    items = [dict(i, text=plain(i["text"]).replace("$", "$$")) for i in _items(read_text(guidelines_path))
             if not i["example"]]
    entries = read_differences(read_text(differences_path))
    where = lambda e: f"{DIFFERENCES.name}:{e['line']} ({e['kind']} | {e['where']})"
    for e in [e for e in entries if e["kind"] == "replace"]:
        if "=>" not in [l.strip() for l in e["body"]]:
            raise ValueError(f"{where(e)}: a replace entry holds the guidelines' words, a line \"=>\", then the model's")
        k = [l.strip() for l in e["body"]].index("=>")
        old, new = " ".join(" ".join(e["body"][:k]).split()), " ".join(" ".join(e["body"][k + 1:]).split())
        hits = sum(i["text"].count(old) for i in items) if old else 0
        if hits != 1:
            raise ValueError(f"{where(e)}: its guidelines words are found {hits} times, not once: \"{old[:90]}\"")
        for i in items:
            if old in i["text"]:
                t = " ".join(i["text"].replace(old, new).split())
                # words left out from the middle of a sentence leave no stray space or comma before its punctuation
                i["text"] = re.sub(r",? +([.,;:)])", r"", t) if not new else t
    items = [i for i in items if i["text"]]
    names = _schema_names(schema_path)
    maps = [tuple(x.strip() for x in l.split("=>")) for e in entries if e["kind"] == "map" for l in e["body"] if l.strip()]
    for i in items:
        t = strip_schema_names(i["text"], names)
        for old, new in maps:
            t = re.sub(rf"(?<![\w-]){re.escape(old)}(?![\w-])", new, t)
        i["text"] = t
    examples = {}
    for e in [e for e in entries if e["kind"] == "examples"]:
        m = re.fullmatch(r"rule (\d+)(?: / (.+))?", e["where"])
        if not m:
            raise ValueError(f"{where(e)}: \"where\" must be \"rule N\" or \"rule N / Part title\"")
        key = (int(m.group(1)), (m.group(2) or "").strip())
        if not any(i["rule"] == key[0] and (i["part"] == key[1] if key[1] else i["level"] == 0) for i in items):
            raise ValueError(f"{where(e)}: the guidelines have no {e['where']} (after the replace entries)")
        examples.setdefault(key, []).extend(_bullets(e["body"]))
    out = []
    for e in [e for e in entries if e["kind"] == "preamble"]:
        out += textwrap.wrap(" ".join(" ".join(e["body"]).split()), width=WIDTH) + [""]
    placed = set()

    def put_examples(key, indent):
        if key in examples and key not in placed:
            placed.add(key)
            for x in examples[key]:
                out.extend(_wrap("Example: " + x, indent + "- ", indent + "  "))

    for n, i in enumerate(items):
        nxt = items[n + 1] if n + 1 < len(items) else None
        if i["level"] == -1:
            while out and not out[-1]:
                out.pop()
            out += ([""] if out else []) + [i["text"].upper(), ""]
            continue
        if i["rule"] is None:                                    # the words section
            out += (_wrap(i["text"], "- ", "  ") if i["level"] == 1 else _wrap(i["text"], "", "") + [""])
            continue
        num = f"{i['rule']}. "
        base = " " * len(num)
        if i["level"] == 0:
            out += _wrap(num + i["text"], "", base)
        else:
            ind = base + "  " * (i["level"] - 1)
            out += _wrap(i["text"], ind + "- ", ind + "  ")
        # a rule's own examples go after its text and before its parts; a part's after the part's last bullet
        if i["level"] == 0:
            put_examples((i["rule"], ""), base)
        elif i["part"] and not (nxt and nxt["rule"] == i["rule"] and nxt["level"] >= 2 and nxt["part"] == i["part"]):
            put_examples((i["rule"], i["part"]), base + "  ")
    unplaced = [k for k in examples if k not in placed]
    if unplaced:
        raise ValueError(f"{DIFFERENCES.name}: examples that found no place: {unplaced}")
    also = [x for e in entries if e["kind"] == "also" for x in _bullets(e["body"])]
    if also:
        out += ["", "ALSO", ""]
        for x in also:
            out += _wrap(x, "- ", "  ")
    text = "\n".join(out).strip("\n") + "\n"
    for word in PERSON_ONLY + tuple(x for x in names if re.fullmatch(r"[A-Z]+(?:_[A-Z]+)+", x)):
        if re.search(rf"(?<![\w]){re.escape(word)}(?![\w])" if word[0].isalnum() and word[-1].isalnum() else re.escape(word), text):
            raise ValueError(f"the model's copy would still hold \"{word}\", which only the person's copy may: "
                             f"add a replace entry to {DIFFERENCES.name}, or word the guidelines by meaning")
    return text


def write_model_copy() -> bool:
    text = build()
    if MODEL_COPY.exists() and read_text(MODEL_COPY) == text:
        return False
    write_text(MODEL_COPY, text)
    return True
