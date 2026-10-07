"""The docs say what the code does: each step guide's Inputs, Settings and
Prompts tables match its run.py and its prompts folder; every file path
named in the docs and code exists; the glossary defines each term once; and
"class" never stands alone (docs/terminology.md: say entity class, subject
class, object class, or component class)."""
import ast
import re
import subprocess
import unittest

from support import ROOT

STEPS = ["010_harvest", "020_clean", "030_split", "040_induce_schema", "050_annotate", "060_extract", "070_evaluate"]
#: Files whose text isn't the project's to sweep: old code, the plan kept as
#: it was written, and the person-made files of annotations/ (except its README).
SKIP = ("to_be_reshaped/", "docs/pipeline_redesign_plan.md", "annotations/")
KEEP = ("annotations/README.md",)


def tracked(*suffixes) -> list:
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    files += [p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("*.py")]     # new files too
    return sorted({f for f in files if f.endswith(suffixes) and (not f.startswith(SKIP) or f in KEEP)
                   and (ROOT / f).exists()})


def panel(step: str) -> dict:
    """INPUTS and SETTINGS of a step's run.py, read without running it."""
    tree = ast.parse((ROOT / step / "run.py").read_text(encoding="utf-8"))
    model = re.search(r'^MODEL = "([^"]+)"', (ROOT / "common" / "common_helpers" / "llm.py").read_text(encoding="utf-8"), re.M)
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id in ("INPUTS", "SETTINGS"):
            values = {}
            for k, v in zip(node.value.keys, node.value.values):
                values[k.value] = model.group(1) if isinstance(v, ast.Name) and v.id == "MODEL" else ast.literal_eval(v)
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

    def test_glossary_terms_once(self):
        text = (ROOT / "docs" / "terminology.md").read_text(encoding="utf-8")
        terms = [t.lower() for t in re.findall(r"^\| \*\*([^*]+)\*\*", text, re.M)]
        self.assertGreater(len(terms), 30)
        self.assertEqual(sorted(t for t in set(terms) if terms.count(t) > 1), [])


if __name__ == "__main__":
    unittest.main()
