"""The docs say what the code does: each step guide's Inputs, Settings and
Prompts tables match its run.py and its prompts folder; every file path
named in the docs and code exists; docs/terminology.md defines each term once;
"class" never stands alone (docs/terminology.md: say entity class, subject
class, object class, or component class); every paper named by its authors
has its title or a link; and the model's prompts quote no ground truth
record."""
import ast
import re
import subprocess
import unittest

from support import EXCLUDED_DIRS, ROOT

STEPS = ["010_harvest", "020_clean", "030_split", "040_induce_schema", "050_annotate", "060_extract", "070_evaluate"]
#: Files whose text isn't the project's to sweep: the archive, and the person-made
#: files of annotations/ (except the READMEs of both).
SKIP = (*EXCLUDED_DIRS, "annotations/")
KEEP = ("annotations/README.md", "archive/README.md")


def tracked(*suffixes) -> list:
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    files += [p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("*.py")]     # new files too
    return sorted({f for f in files if f.endswith(suffixes) and (not f.startswith(SKIP) or f in KEEP)
                   and (ROOT / f).exists()})


def panel(step: str) -> dict:
    """INPUTS and SETTINGS of a step's run.py, read without running it."""
    tree = ast.parse((ROOT / step / "run.py").read_text(encoding="utf-8"))
    llm = (ROOT / "common" / "common_helpers" / "llm.py").read_text(encoding="utf-8")
    named = {n: re.search(rf'^{n} = "([^"]+)"', llm, re.M).group(1) for n in ("MODEL", "DRAFTING_MODEL", "SERVICE", "THINKING")}  # defaults from llm.py
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id in ("INPUTS", "SETTINGS"):
            values = {}
            for k, v in zip(node.value.keys, node.value.values):
                values[k.value] = named[v.id] if isinstance(v, ast.Name) and v.id in named else ast.literal_eval(v)
            out[node.targets[0].id] = values
    return out


def table(guide: str, heading: str) -> list:
    """The rows of the first table under a "## heading" of a guide: [[cells]]."""
    text = (ROOT / guide).read_text(encoding="utf-8")
    section = text.split(f"\n## {heading}\n", 1)[1].split("\n## ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("|")]
    return [[c.strip() for c in row.strip("|").split("|")] for row in rows[2:]]


def shown(value) -> str:
    """A setting's default as a guide writes it."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return "empty" if value == "" else str(value)


class Guides(unittest.TestCase):

    def test_settings_tables(self):
        for step in STEPS:
            with self.subTest(step=step):
                rows = table(f"{step}/{step}.md", "Settings")
                written = {r[0].strip("`"): r[1].strip("`") for r in rows}
                self.assertEqual(written, {k: shown(v) for k, v in panel(step).get("SETTINGS", {}).items()})

    def test_inputs_tables(self):
        for step in STEPS:
            inputs = panel(step).get("INPUTS", {})
            if not inputs:
                continue
            with self.subTest(step=step):
                rows = table(f"{step}/{step}.md", "Inputs")
                written = {r[0].strip("`"): r[1].split(" (in Git)")[0].strip("`") for r in rows}
                self.assertEqual(written, inputs)

    def test_prompts_tables(self):
        for step in STEPS:
            folder = ROOT / step / f"{step}_prompts"
            files = sorted(p.name for p in folder.glob("*.txt")) if folder.exists() else []
            with self.subTest(step=step):
                rows = table(f"{step}/{step}.md", "Prompts")
                listed = sorted({re.sub(r"^`.*/", "`", r[0]).strip("`") for r in rows if r[0].strip("`").endswith(".txt")})
                shared = {p.name for p in (ROOT / "common" / "common_prompts").glob("*.txt")}
                self.assertEqual([x for x in listed if x not in shared], files)

    def test_every_prompt_used(self):
        code = "\n".join((ROOT / f).read_text(encoding="utf-8") for f in tracked(".py") if not f.startswith("tests/"))
        for prompt in sorted(ROOT.glob("*/*_prompts/*.txt")):
            with self.subTest(prompt=prompt.name):
                self.assertIn(f'"{prompt.name}"', code)


TOP = tuple(STEPS) + ("common", "helpers", "docs", "annotations", "tests")
PATH = re.compile(r"(?<![\w./-])((?:%s)/[\w./-]*\w)" % "|".join(TOP))


def outputs_named(step: str) -> str:
    """The text of a step's code, where the names of its output files appear."""
    return "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / step).rglob("*.py"))


class Paths(unittest.TestCase):

    def test_paths_exist(self):
        missing = []
        for f in tracked(".md", ".txt", ".py"):
            text = (ROOT / f).read_text(encoding="utf-8-sig")
            for m in PATH.finditer(text):
                p = m.group(1).rstrip(".")
                if text[m.end():m.end() + 1] in ("<", "*", "{"):
                    continue                                                       # a pattern: batch_<N>.csv
                if (ROOT / p).exists() or re.search(r"batch_\d+\.(csv|json)$", p):     # an example batch file
                    continue
                module = re.fullmatch(r"(.+\.py)\.(\w+)", p.replace(".", ".py.", 1) if not p.endswith(".py") else p)
                if module and (ROOT / module.group(1)).exists() and \
                        re.search(rf"^(def |class |){module.group(2)}\b", (ROOT / module.group(1)).read_text(encoding="utf-8"), re.M):
                    continue                                                       # module.function
                step, _, name = p.partition("/")
                if step in STEPS and "/" not in name and name in outputs_named(step):
                    continue                                                       # an output file, in outputs/intermediate_results/
                missing.append(f"{f}:{text.count(chr(10), 0, m.start()) + 1}: {p}")
            if f.endswith(".md"):
                for m in re.finditer(r"\]\(([^)#\s]+)(#[^)]*)?\)", text):
                    if not m.group(1).startswith(("http", "mailto")) and not ((ROOT / f).parent / m.group(1)).exists():
                        missing.append(f"{f}: link {m.group(1)}")
        self.assertEqual(missing, [])


class Vocabulary(unittest.TestCase):

    QUALIFIED = re.compile(r"(entity|subject|object|component|describes)[\s#*>`-]+$", re.I)
    BARE = re.compile(r"(?<![\w-])([Cc]lass|[Cc]lasses)\b(?![\w-])")     # not CLASSES: the old section heading

    def test_no_bare_class(self):
        found = []
        for f in tracked(".md", ".txt", ".py", ".html"):
            if f == "tests/test_docs.py":
                continue                                                       # this file talks about the word
            text = (ROOT / f).read_text(encoding="utf-8-sig")
            if f.endswith(".py"):
                text = re.sub(r'"\s*\n\s*f?"', "", text)                         # strings continued on the next line
            if f.endswith(".md"):                                              # a fenced block is code (a diagram's own
                text = re.sub(r"```.*?```", lambda b: "\n" * b.group(0).count("\n"), text, flags=re.S)   # `class`), not prose
            for m in self.BARE.finditer(text):
                start = text.rfind("\n", 0, m.start()) + 1
                line = text[start:text.find("\n", m.start())]
                if self.QUALIFIED.search(text[max(0, m.start() - 40):m.start()]):
                    continue
                if text[m.start() - 1:m.start()] == '"' and text[m.end():m.end() + 1] == '"':
                    continue                                                   # the word itself, quoted
                if f.endswith((".py", ".html")) and re.search(r"^\s*class \w|\bclass\s*[=:]|className|dataclass", line):
                    continue                                                   # Python and HTML's own word
                found.append(f"{f}:{text.count(chr(10), 0, m.start()) + 1}: {line.strip()[:120]}")
        self.assertEqual(found, [])

    def test_no_field_words(self):
        """The docs use only docs/terminology.md's words, not the research field's for the same things (FIELD_WORDS
        says which, and what to write instead), outside the places FIELD_WORDS_ALLOWED lists."""
        self.assertEqual(field_words_found(), [])

    def test_field_words_near_misses(self):
        """What counts and what doesn't, on made-up text: (file kind, text, how many field words are reported)."""
        cases = [
            ("a.md", "The model finds each relation in the text.", 1),
            ("a.md", "Pass the argument --schema.", 1),                      # in a doc, never a Python argument
            ("a.md", "two triplets, two mentions, a span, its boundaries", 4),
            ("a.md", "It requires \"both arguments' entity types\" to match.", 2),   # a quote with no meaning given
            ("a.md", "what \"Boundaries\" counts", 1),                         # a quoted word alone needs it too
            ("a.md", "A resumed harvest spans several days.", 1),              # the verb too
            ("a.txt", "predicates (kinds of relations)", 1),
            ("a.py", "# the relation it\n# expresses\nx = 1\n", 1),
            ("a.py", "x = (\"a wrong entity \"\n     \"type\")\n", 1),             # strings joined: "entity type"
            ("a.html", "<p>A new relation between two things</p>", 1),
            ("a.md", "A relationship between two things; records mentioning a value; it was mentioned.", 0),
            ("a.md", "an entity class, entity classes, entity-class accuracy, HAS_TIME_SPAN", 0),
            ("a.md", "relation classification, relation\nextraction", 0),
            ("a.md", "Pink et al. (2014), \"Analysing recall loss in named entity slot filling\", EMNLP", 0),
            ("a.md", "S. Wadhwa, \"Revisiting Relations,\" in *Proceedings of ACL*", 0),
            ("a.md", "Smith, \"Arguments and Spans\" ([paper](https://example.org/x))", 0),
            ("a.md", "\"both arguments' [the subject instance's and the object instance's] entity types [entity "
                     "classes]\"", 0),
            ("a.md", "\"Boundaries\" [the words right, entity classes not checked]", 0),
            ("a.md", "`entity`, [predicates](x/relations.md), https://x.org/entity\n```\nspan\n```", 0),
            ("a.md", "an HTML entity, a word boundary, a code span", 0),
            ("a.txt", "too vague (e.g. \"Thing\", \"Entity\")", 0),               # a label, quoted
            ("a.py", "def f(argument):\n    \"\"\"Its argument's span.\"\"\"\n    return {\"entity\": argument}\n", 0),
        ]
        for rel, text, n in cases:
            with self.subTest(text=text):
                self.assertEqual(len(field_words_in(rel, text)), n, field_words_in(rel, text))

    def test_terms_defined_once(self):
        text = (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8")
        terms = [t.lower() for t in re.findall(r"^\| \*\*([^*]+)\*\*", text, re.M)]
        self.assertGreater(len(terms), 30)
        self.assertEqual(sorted(t for t in set(terms) if terms.count(t) > 1), [])


#: The research field's words for things docs/terminology.md names otherwise: (the word, what to write instead).
#: The docs, the prompts, and the code's comments and strings use only terminology.md's words. Matched as whole
#: words, case ignored; "entity-class", "HAS_TIME_SPAN", and `entity` (code) are other words. "relationship" is
#: plain English and allowed, and so are "mentioned" and "mentioning" (only verbs; "mention" can be the field's noun).
FIELD_WORDS = [
    (r"arguments?", "the subject instance and the object instance"),
    (r"entity\s+types?", "entity class(es)"),
    (r"named\s+entit(?:y|ies)", "subject instance or object instance"),
    (r"entit(?:y|ies)(?!\s+class)", "subject instance or object instance (a thing), or entity class (a kind)"),
    (r"relation\s+types?", "predicate"),
    (r"relations?(?!\s+(?:classification|extraction))", "predicate (a schema entry), or, in plain English, relationship; "
                                                       "relation classification and relation extraction are terms"),
    (r"boundar(?:y|ies)", "the words of a subject instance or object instance"),
    (r"triplets?", "triple(s)"),
    (r"mentions?", "a wording, or a verb such as names or says"),
    (r"spans?", "a passage, the source text, or the words"),
    (r"slot[\s-]+filling", "say what is done, in terminology.md's words"),
]
FIELD_WORD = re.compile(r"(?<![\w`-])(?:%s)(?![\w`-])" % "|".join(w for w, _ in FIELD_WORDS), re.I)
#: Where a field word is allowed. Everywhere:
#:   - a paper's title, in a citation: a quoted passage followed by its venue or link ("…", EMNLP / ," in *… /
#:     ([paper](…)); the field's name for itself, relation extraction, is a term (terminology.md, section 6);
#:   - a phrase with another meaning: HTML entity, word boundary, code span.
#: In the docs (*.md): code (fenced blocks, `code spans`, link targets) isn't read; a direct quote may hold a field
#: word only when the word is followed at once by its meaning in our words in square brackets:
#:   "both arguments' [the subject instance's and the object instance's] entity types [entity classes]".
#: In the prompts (*.txt) and code (*.py: comments and strings only; *.html): a quoted word alone is a label or a
#: key ("Entity", a too vague label; "entity", a key of step 040's files), not prose. In code only: argument(s)
#: (a function's or the command line's) and span(s) (an HTML tag; a regular expression match's span()).
FIELD_WORDS_ALLOWED_PHRASES = re.compile(r"HTML\s+entit(?:y|ies)|word\s+boundar(?:y|ies)|code\s+spans?", re.I)
FIELD_WORDS_ALLOWED_IN_CODE = re.compile(r"arguments?|spans?", re.I)
#: Files not swept: this file (it lists the words), and the archive's old notes and code (kept as they were written) and local notes.
FIELD_WORDS_SKIP = ("tests/test_docs.py", *EXCLUDED_DIRS)
TITLE_AFTER = re.compile(r"\s*,?\s*(?:in\s+\*|[A-Z][A-Za-z]*[A-Z]\w*\b|\(?\[paper\]\(|arXiv|doi:)")
GLOSS_AFTER = re.compile(r"(?:'s|'|’s|’)?[\"”]?\s*\[[^\]\n]+\](?!\()")


#: The parts of a question (annotations/questions_for_experts.md) that quote other files word for word: a record's
#: text, definitions, rows of the translation table, rules, a pipeline method's words, and the Affects list.
QUOTE_SECTIONS = re.compile(r"^### (Example record|Ground truth schema|Translation table|Annotation guidelines"
                            r"|Pipeline method|Affects)\s*$")


def quotes_blanked(text: str) -> str:
    """The questions file with its quoting parts (QUOTE_SECTIONS) blanked out, line numbers kept."""
    out, quoting = [], False
    for line in text.split("\n"):
        if line.startswith("#"):
            quoting = bool(QUOTE_SECTIONS.match(line))
            out.append(line)
        else:
            out.append(re.sub(r"[^\n]", " ", line) if quoting else line)
    return "\n".join(out)


def field_word_texts(rel: str, text: str) -> list:
    """[(first line, text)]: the parts of a file a person reads. A doc or prompt: all of it, with code and link
    targets blanked out in a doc (line numbers kept). Python: each comment (a run of comment lines joined) and each
    string, an f-string's {…} as {}. HTML: all of it."""
    import io
    import tokenize
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))           # noqa: E731
    if rel == "annotations/questions_for_experts.md":                  # its quotes are others' words, checked
        text = quotes_blanked(text)                                    # against their sources by the review page
    if rel.endswith(".md"):
        text = re.sub(r"```.*?```", blank, text, flags=re.S)
        text = re.sub(r"`[^`\n]*`", blank, text)
        text = re.sub(r"(?<=\]\()[^)\n]*(?=\))", blank, text)
        text = re.sub(r"https?://\S+", blank, text)
    if not rel.endswith(".py"):
        return [(1, text)]
    parts, inner = [], set()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)                 # a stray escape in a string isn't our concern
        tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            inner |= {id(v) for v in node.values}
            parts.append((node.lineno, "".join(v.value if isinstance(v, ast.Constant) else "{}" for v in node.values)))
    parts += [(n.lineno, n.value) for n in ast.walk(tree)
              if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in inner]
    run, last = None, -1
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            if run and tok.start[0] == last + 1:
                run[1] += " " + tok.string.lstrip("#")
            else:
                run = [tok.start[0], tok.string.lstrip("#")]
                parts.append(run)
            last = tok.start[0]
    return [tuple(p) for p in parts]


def field_words_found() -> list:
    """["file:line: word (write instead: …): the line"]: each field word, in every file swept, outside the places it
    is allowed."""
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    files += [p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("*.py")]
    return [f for rel in sorted(set(files))
            if rel.endswith((".md", ".txt", ".py", ".html")) and (not rel.startswith(FIELD_WORDS_SKIP) or rel in KEEP)
            and (ROOT / rel).exists()
            for f in field_words_in(rel, (ROOT / rel).read_text(encoding="utf-8-sig"))]


def field_words_in(rel: str, whole: str) -> list:
    """The field words of one file's text outside the places allowed (`rel` says the file's kind by its extension)."""
    found, doc, code = [], rel.endswith(".md"), rel.endswith((".py", ".html"))
    quoted = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”" + (r"|'[^'\n]*'" if code else ""))
    for first, text in field_word_texts(rel, whole):
        allowed = [m.span() for m in FIELD_WORDS_ALLOWED_PHRASES.finditer(text)]
        quotes = [m.span() for m in quoted.finditer(text)]
        for m in FIELD_WORD.finditer(text):
            if any(a <= m.start() < b for a, b in allowed) or (code and FIELD_WORDS_ALLOWED_IN_CODE.fullmatch(m.group(0))):
                continue
            if rel.endswith(".py") and text.strip().lower() == m.group(0).lower():
                continue                                                       # a string that is the word alone: a key
            quote = next(((a, b) for a, b in quotes if a < m.start() < b), None)
            if quote and TITLE_AFTER.match(text, quote[1]):
                continue                                                       # a paper's title
            if quote and not doc and text[quote[0] + 1:quote[1] - 1].strip().lower() == m.group(0).lower():
                continue                                                       # a label or key, quoted
            if quote and doc and GLOSS_AFTER.match(text, m.end()):
                continue                                                       # a quote, with its meaning in brackets
            line = text[text.rfind("\n", 0, m.start()) + 1:].split("\n", 1)[0]
            instead = next(i for w, i in FIELD_WORDS if re.fullmatch(w, m.group(0), re.I))
            found.append(f"{rel}:{first + text.count(chr(10), 0, m.start())}: {m.group(0)} "
                         f"(write instead: {instead}): {line.strip()[:120]}")
    return found


#: The docs whose terms link to docs/terminology.md (every non-code doc except the prompts,
#: terminology.md itself, and the person-made files of annotations/).
LINKED_DOCS = ["README.md", "070_evaluate/metrics.md", "annotations/guidelines.md", *(f"070_evaluate/metrics/{n}.md" for n in ("pairs", "precision", "recall", "f1", "entity_class_accuracy", "recall_upper_bound", "recall_within_reach", "describes", "approximately")), "annotations/README.md", "helpers/audit.md", "tests/README.md",
               "docs/running_on_nasa_laptop.md", "docs/virtual_environment_setup.md", "docs/upkeep.md"] + [f"{s}/{s}.md" for s in STEPS]
#: Multi-word terms whose bold in terminology.md marks emphasis or an everyday phrase, not a separate term;
#: and terms that also read as an everyday phrase ("records outside the ground truth only"), checked by hand.
NOT_TERMS = {"same fact", "not the same fact", "now exists", "whole records", "within the pool's strata", "main moves",
             "relationship type", "ground truth triples", "ground truth only", "extracted only"}


def slug(heading: str) -> str:
    """GitHub's anchor for a heading."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def multiword_terms() -> list:
    """The multi-word terms of docs/terminology.md (first column, and those defined in bold inside an entry):
    unambiguous enough for a test to tell a use of the term from an everyday phrase."""
    text = (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8")
    names = set()
    for line in text.splitlines():
        m = re.match(r"^\| (.*?) \| (.*) \|$", line)
        if m and "**" in m.group(1):
            names |= {n for n in re.findall(r"\*\*([^*]+)\*\*", line) if " " in n.strip()}
    return sorted({n.strip().lower() for n in names} - NOT_TERMS, key=len, reverse=True)


class TermLinks(unittest.TestCase):
    """Each term has one home (docs/terminology.md, or the doc it points to); the docs link to it."""

    #: Not read for first uses: code, links, HTML, web addresses, *italic names*, and "quoted passages" (a quote or a
    #: paper's title is someone else's words: no link goes inside it).
    PROTECT = re.compile(r"`[^`\n]*`|\[[^\[\]\n]*\]\([^)\n]*\)|<[^>\n]+>|https?://\S+|(?<![*\w])\*(?!\*)[^*\n]+\*(?![*\w])"
                         r'|"[^"\n]*"|“[^”\n]*”')

    def test_anchors_exist(self):
        """Every link to a heading of a doc (e.g. terminology.md#2-triples) lands on a heading that exists."""
        bad = []
        for rel in LINKED_DOCS + ["docs/terminology.md"]:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for m in re.finditer(r"\]\(([^)#\s]+\.md)?#([\w-]+)\)", text):
                target = ((ROOT / rel).parent / m.group(1)).resolve() if m.group(1) else (ROOT / rel)
                headings = {slug(h) for h in re.findall(r"^#{1,6} (.+)$", target.read_text(encoding="utf-8"), re.M)}
                if m.group(2) not in headings:
                    bad.append(f"{rel}: #{m.group(2)} not a heading of {target.name}")
        self.assertEqual(sorted(set(bad)), [])

    def test_first_use_linked(self):
        """In each section (headings of level 1 to 3), the first use of a multi-word term is a link
        (code, headings, table header rows, and italic names don't count)."""
        self.assertEqual(first_uses_unlinked(), [])

    def test_one_link_per_term_per_section(self):
        """A term links once per section, and never from its own home back to terminology.md (which only
        points back): there it links within the page, or not at all in its own section."""
        homes, extra = term_homes(), []
        for rel in LINKED_DOCS:
            seen = set()
            for i, line in enumerate((ROOT / rel).read_text(encoding="utf-8").split("\n"), 1):
                if is_section_heading(line):
                    seen = set()
                for m in re.finditer(r"\[([^\[\]\n]*)\]\([^)]*terminology\.md#[\w-]+\)", line):
                    t = term_key(m.group(1))
                    if homes.get(t) == rel:
                        extra.append(f"{rel}:{i}: {m.group(1)} links to terminology.md from its own home")
                    elif t in seen:
                        extra.append(f"{rel}:{i}: {m.group(1)} linked twice in one section")
                    seen.add(t)
        self.assertEqual(extra, [])


def is_section_heading(line: str) -> bool:
    """A heading that starts a section for linking: level 1 to 3, and not a part heading such as
    *Definition* or *Assumes and can't see* (written <ins>…</ins>), which stays in its section."""
    h = re.match(r"^(#{1,6}) (.*)", line)
    return bool(h) and len(h.group(1)) <= 3 and "<ins>" not in h.group(2)


def term_key(text: str) -> str:
    """The term a link's text names, plurals and case folded ("Records" -> "record")."""
    t = text.lower().strip()
    t = {"strata": "stratum", "entries": "entry"}.get(t, t)
    t = re.sub(r"classes$", "class", t)
    return re.sub(r"(?<!s)s$", "", t)


def term_homes() -> dict:
    """{term: the doc that defines it}, for the entries of terminology.md that point elsewhere ("See [`x.md`…")."""
    homes = {}
    for line in (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (.*?) \| (?:[^|]*?)?[Ss]ee \[`([^`]+\.md)`", line)
        if m:
            for n in re.findall(r"\*\*([^*]+)\*\*", line):
                homes[n.strip().lower()] = m.group(2)
    return homes


def first_uses_unlinked() -> list:
    """[(doc, line, term, column)]: first uses of a multi-word term, per section, that aren't a link."""
    if True:
        homes = term_homes()
        # the NOT_TERMS phrases are matched too, as units, so no shorter term counts inside them
        # ("ground truth" in "ground truth only"), but they are never reported
        terms = sorted(set(multiword_terms()) | NOT_TERMS, key=len, reverse=True)
        # a term may sit at the edge of a [unit] (metrics.md: square brackets mark one unit), but not of a link's text
        forms = [(t, re.compile(r"(?<![\w\-/.#`_])(" + re.escape(t) + r"(?:e?s)?)(?![\w\-`_]|\]\()", re.I)) for t in terms]
        missing = []
        for rel in LINKED_DOCS:
            lines = (ROOT / rel).read_text(encoding="utf-8").split("\n")
            linked, fence = set(), False
            for i, line in enumerate(lines):
                if line.lstrip().startswith("```"):
                    fence = not fence
                    continue
                h = re.match(r"^(#{1,6}) ", line)
                if fence or re.match(r"^( {4}|\t)(?![-*\d])", line) or h:
                    if is_section_heading(line):
                        linked = set()
                    continue
                if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1]):
                    continue
                for m in re.finditer(r"\[([^\[\]\n]*)\]\([^)\n]+\)", line):           # to terminology.md, or to the term's home
                    linked |= {t for t, rx in forms if rx.fullmatch(m.group(1))}
                plain = TermLinks.PROTECT.sub(lambda m: " " * len(m.group(0)), line)
                taken = []
                for t, rx in forms:
                    for m in rx.finditer(plain):
                        if any(a < m.end() and m.start() < b for a, b in taken):
                            continue
                        taken.append(m.span())
                        if t not in linked and t not in NOT_TERMS and homes.get(t) != rel:
                            missing.append((rel, i + 1, t, m.start()))
                            linked.add(t)
        return missing


class NoLinkInCode(unittest.TestCase):
    """A link inside a code span breaks it (`metrics/[pairs](…).md` is no longer a path)."""

    def test_no_link_inside_a_code_span(self):
        found = []
        for path in (ROOT / f for f in tracked(".md")):
            fence = False
            for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
                if line.startswith("```"):
                    fence = not fence
                    continue
                if not fence:
                    found += [f"{path.relative_to(ROOT).as_posix()}:{n}: {m.group(0)}"
                              for m in re.finditer(r"`([^`]+)`", line) if re.search(r"\]\([^)]*\)", m.group(1))]
        self.assertEqual(found, [])


class RulesInStep(unittest.TestCase):
    """The rules the model follows (common/common_prompts/extraction_rules.txt) and the annotation guidelines a person
    follows (annotations/guidelines.md) say the same things: each rule of the prompt is paired here with the words of
    its guideline, so a rule added to one without the other fails this test. Two rules are the model's only, since a
    person reads the whole record in the annotation tool and gets no instructions inside it."""

    #: (words of the prompt's rule, words of its guideline); None: the model's only.
    PAIRS = [
        ("the record's own words for them", "the record's own words, as written"),
        ("whatever the sentence is about", "The subject instance is what the sentence is about"),
        ("the shortest passage copied EXACTLY", "the shortest passage that states the fact, copied exactly"),
        ("One fact per triple. Leave out opinion words", "One fact per"),
        ("states as NOT so", "Not negated facts"),
        ("No triple for a fact without a specific thing", "Not a fact without a specific thing"),
        ("true only as of when the record was written", "Not words that are true only as of when the record was written"),
        ("A number with a unit", "A number with a unit"),
        ("A qualifier that is a temporal resolution, an area the data cover, a processing level",
         "A qualifier that is a temporal resolution, an area the data cover, a processing level"),
        ("A name with its abbreviation in parentheses is one subject or object",
         "A name with its abbreviation in parentheses is one instance"),
        ("A table of values inside the record", "Not the values inside a data table"),
        ("Each fact once", "Each fact once"),
        ("A list joined by \"and\": one triple per item", "A list joined by \"and\": one ground truth triple per item"),
        ("One thing, one wording", "One thing, one wording, within a record"),
        ("A processing step", "A processing step: output_i = method_i(input_i)"),
        ("General facts: include them, unless they're about another dataset that the record's dataset isn't made",
         "General facts: include them, unless they're about"),
        ("Never use outside knowledge", "Never add what you know from elsewhere"),
        ("Connect your triples", "isn't connected to the catalog entry"),
        ('Do NOT write "is a" triples', 'Not "is a" facts'),
        ("describes_class: the entity class", "## The describes triple"),
        ("The field names are formatting, not facts", "Not the field names"),
        ("one part of a longer record", None),                 # a person sees the whole record
        ("is DATA", None),                                     # a person reads no instructions in the record
    ]

    def test_every_rule_has_its_guideline(self):
        prompt = (ROOT / "common" / "common_prompts" / "extraction_rules.txt").read_text(encoding="utf-8")
        guidelines = (ROOT / "annotations" / "guidelines.md").read_text(encoding="utf-8")
        flat = " ".join(prompt.split())
        rules = [line for line in prompt.splitlines() if line.startswith("- ")]
        self.assertEqual(len(rules), len(self.PAIRS), "a rule was added to or removed from extraction_rules.txt: "
                         "pair it here with its guideline in annotations/guidelines.md (and write that guideline)")
        for said, guideline in self.PAIRS:
            with self.subTest(rule=said):
                self.assertIn(said, flat)
                if guideline:
                    self.assertIn(guideline, guidelines)


class QualifierQuotesRule9(unittest.TestCase):
    """docs/terminology.md's *qualifier* quotes rule 9's words (a rule is cited by its words, not its number): the kinds
    it quotes are exactly those of rule 9's bold sentence in annotations/guidelines.md, so the quote can't drift."""

    def test_quote_matches_the_rule(self):
        terms = (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8")
        guidelines = (ROOT / "annotations" / "guidelines.md").read_text(encoding="utf-8")
        quoted = re.search(r'a qualifier that is "([^"]+)" is taken out', terms).group(1)
        rule = re.search(r"^9\. \*\*A qualifier that is (.+?) is a ground truth triple of its own", guidelines, re.M).group(1)
        self.assertEqual(quoted, rule)


#: A paper named by its authors: "Taillé et al." (any year, or none), or two or more surnames joined by & or "and"
#: and followed by a year ("Zhang & Soh 2024", "Guest, Bunce & Johnson (2006)").
CITE_NAME = r"[A-Z][\w'’-]*[a-zà-ÿ][\w'’-]*"
CITE_MENTION = re.compile(rf"\b({CITE_NAME}) et al\.|\b({CITE_NAME})(?:, {CITE_NAME})*,? (?:&|and) {CITE_NAME},? \(?(?:1[89]|20)\d\d\b")
#: The same authors anywhere in a full citation (year or not), so a later short mention of them is allowed.
CITE_AUTHORS = re.compile(rf"\b({CITE_NAME})(?:, {CITE_NAME})*,? (?:&|and) {CITE_NAME}\b|\b({CITE_NAME}) et al\.")
#: What makes a citation full: a link to the paper, a quoted title, an italic title, an arXiv number, a DOI, or a
#: numbered reference ([5]).
CITE_FULL = re.compile(r"\]\((?:https?:|[^)\s]*\.pdf\b)|\"[^\"\n]{8,}\"|“[^”\n]{8,}”|(?<![*\w])\*[^*\n]{6,}\*(?!\*)"
                       r"|arXiv|doi:|\[\d+(?:,\s*\d+)*\]|https?://")
#: Sentence ends, not after "et al", "e.g", "i.e", "vs", "ch", "pp", "ed", "eds", "no".
CITE_SENTENCE = re.compile(r"(?<!\bal)(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)(?<!\bch)(?<!\bpp)(?<!\bed)(?<!\beds)(?<!\bno)"
                           r"[.;]\s+(?=[A-Z*\"“(\[])")


def citations_without_source() -> list:
    """["file:line: mention: the line"]: each paper named by its authors with no title or link in its sentence, when
    the same doc gives no full citation of those authors elsewhere either."""
    found = []
    for rel in tracked(".md"):
        if rel.startswith(FIELD_WORDS_SKIP) and rel not in KEEP:
            continue
        text = re.sub(r"```.*?```", lambda m: re.sub(r"[^\n]", " ", m.group(0)), (ROOT / rel).read_text(encoding="utf-8"),
                      flags=re.S)
        # a numbered reference ("[12] P. Koehn, ...") is one citation: its publisher ("Chapman & Hall, 1993") is no mention
        sentences = [(n, s) for n, line in enumerate(text.split("\n"), 1)
                     for s in ([line] if re.match(r"\[\d+\] ", line) else CITE_SENTENCE.split(line))]
        cited = {(a.group(1) or a.group(2)).lower() for _, s in sentences if CITE_FULL.search(s)
                 for a in CITE_AUTHORS.finditer(s)}
        for n, s in sentences:
            if CITE_FULL.search(s):
                continue
            found += [f"{rel}:{n}: {m.group(0)}: {s.strip()[:120]}" for m in CITE_MENTION.finditer(s)
                      if (m.group(1) or m.group(2)).lower() not in cited]
    return found


class Citations(unittest.TestCase):
    """Every paper the docs name by its authors has its title or a link in the same sentence, or the same doc gives
    its full citation elsewhere (a repeated mention may then be short), so every borrowed idea can be found."""

    def test_every_author_mention_has_a_source(self):
        found = citations_without_source()
        self.assertFalse(found, "\n" + "\n".join(f"{f} (give the title or a link, as the metric pages do)" for f in found))

    def test_the_check_sees_short_mentions(self):
        """A near miss: the same mention, alone, is caught; with a title, or after a full citation, it isn't."""
        short = "Agreement was measured (Hripcsak & Rothschild 2005)."
        self.assertTrue(list(CITE_MENTION.finditer(short)))
        self.assertFalse(CITE_FULL.search(short))
        self.assertTrue(CITE_FULL.search('Hripcsak & Rothschild (2005), "Agreement, the F-Measure, and Reliability"'))
        self.assertEqual(CITE_SENTENCE.split("Taillé et al. (2020) say so. Then"), ["Taillé et al. (2020) say so", "Then"])


class PromptsQuoteNoGroundTruth(unittest.TestCase):
    """The model's prompts use invented examples, never text from ground truth records: a prompt that quotes a ground
    truth record could hand the model an answer it is scored on. Every quoted phrase of 3 or more words in a prompt
    file ("..." or '...') must occur in no subject, object (the describes triples' objects are the titles), or
    source_text of annotations/ground_truth/, and no run of 5 words of a prompt file
    occurs in one."""

    def test_no_quote_from_ground_truth(self):
        import csv
        prompts = sorted(p for p in ROOT.glob("*/*_prompts/*.txt")
                         if not p.relative_to(ROOT).as_posix().startswith(EXCLUDED_DIRS))
        truth = sorted((ROOT / "annotations" / "ground_truth").glob("*.csv"))
        self.assertTrue(prompts, "no prompt files found under */*_prompts/")
        self.assertTrue(truth, "no ground truth files found in annotations/ground_truth/")
        flat = lambda s: " ".join(s.split()).lower()
        texts = []
        for path in truth:
            with open(path, encoding="utf-8-sig", newline="") as fh:
                rows = list(csv.DictReader(fh))
            self.assertTrue(rows, f"{path.relative_to(ROOT).as_posix()} has no rows")
            texts += [flat(row[k]) for row in rows for k in ("subject", "object", "source_text")]
        found, quotes = [], 0
        for path in prompts:
            text = " ".join(path.read_text(encoding="utf-8").split())
            for q in re.findall(r'"([^"]+)"', text) + re.findall(r"(?<!\w)'([^']+?)'(?!\w)", text):
                if len(q.split()) >= 3:
                    quotes += 1
                    found += [f"{path.relative_to(ROOT).as_posix()}: \"{q}\" is in a ground truth record; "
                              f"replace it with an invented example of the same shape"] * any(flat(q) in t for t in texts)
        self.assertTrue(quotes, "no quoted phrase of 3 or more words found in the prompts: the test would check nothing")
        self.assertFalse(found, "\n" + "\n".join(found))

    def test_no_five_word_run_from_ground_truth(self):
        """Unquoted copying too: no run of 5 consecutive words of a prompt file (case, spacing, and punctuation
        ignored) occurs in a ground truth subject, object, or source_text."""
        import csv
        prompts = sorted(p for p in ROOT.glob("*/*_prompts/*.txt")
                         if not p.relative_to(ROOT).as_posix().startswith(EXCLUDED_DIRS))
        truth = sorted((ROOT / "annotations" / "ground_truth").glob("*.csv"))
        self.assertTrue(prompts, "no prompt files found under */*_prompts/")
        self.assertTrue(truth, "no ground truth files found in annotations/ground_truth/")
        words = lambda s: re.sub(r"\W+", " ", s.lower()).split()
        runs = lambda w: {" ".join(w[i:i + 5]) for i in range(len(w) - 4)}
        truth_runs = set()
        for path in truth:
            with open(path, encoding="utf-8-sig", newline="") as fh:
                for row in csv.DictReader(fh):
                    for k in ("subject", "object", "source_text"):
                        truth_runs |= runs(words(row[k]))
        self.assertTrue(truth_runs, "no 5-word run found in the ground truth: the test would check nothing")
        found = [f"{path.relative_to(ROOT).as_posix()}: \"{r}\" is in a ground truth record; "
                 f"replace the passage with an invented example sharing no 5-word run with any record"
                 for path in prompts for r in sorted(runs(words(path.read_text(encoding="utf-8"))) & truth_runs)]
        self.assertFalse(found, "\n" + "\n".join(found))


if __name__ == "__main__":
    unittest.main()
