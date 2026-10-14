"""kg_check.py

Checks that the knowledge graph in kg/ agrees with the code, and writes
kg/index.md from the node files.

    python kg_check.py                 # list the problems; exit 1 when there are any
    python kg_check.py --write-index   # rewrite kg/index.md, then run the checks

It reports a problem when:

- an [[ID]] link points to a node that does not exist, or an ID is defined twice,
- a source file has no MOD node,
- a node marked [C] cites no evidence, or cites something that is not a test,
- a cited test name does not exist in tests/,
- a node marked [H] names no node that replaced, closed or moved it,
- a constant's value in kg/rules.md differs from the value in the code or in the
  customer file (a RUL node with a .toml File names its Key),
- a constant in kg/rules.md has no Kind, or one that is not parameter or label,
- a public constant in the code, or a setting in the customer file, has no RUL node,
- a measure's Function does not exist,
- a RES node names no table in docs/results.md, or names one that is not there,
- a [C] node gives "review" as its evidence but is not a policy node (Kind: policy),
- a field line is longer than 240 characters, or a node has more than 8 fields,
- a decision sits outside the two groups the index is built from,
- kg/index.md differs from what --write-index would write, or has over 3,000 words.

A Commit field is information and not evidence. When the git history is present and a cited commit
is not in it, the checker warns. It never fails on that, because the history may be recreated.
tests/test_kg.py runs the same checks.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import operator
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KG_DIR = ROOT / "kg"
CUSTOMER_FILE = "customers/demo.toml"  # its settings outside [[hotels]] are constants too
NODE_FILES = {
    "modules.md": "Modules",
    "data.md": "Data",
    "rules.md": "Rules and constants",
    "shocks.md": "Shocks",
    "concepts.md": "Concepts",
    "measures.md": "Measures",
    "sources.md": "Sources",
    "decisions.md": "Decisions",
    "results.md": "Results",
    "forks.md": "Open forks",
    "unknowns.md": "Unknowns",
}
PREFIXES = ("MOD", "DAT", "RUL", "SHK", "CON", "MEA", "SRC", "DEC", "RES", "FRK", "UNK")
STATUSES = "CTPOUH"
KINDS = ("parameter", "label")
DECISION_GROUPS = ("Market and agent design", "Engineering")
HISTORY_KEYS = ("Replaced by", "Closed by", "Moved to")  # what an [H] node must link to
REVIEW, POLICY = "review", "policy"  # the evidence a policy node may give, and its Kind
FIELD_LIMIT = 240  # characters in one field line
FIELD_COUNT_LIMIT = 8  # field lines in one node
RESULTS_FILE = "docs/results.md"  # where a RES node's table lives
TABLE_CAPTION = re.compile(r'"([^"]+)"')  # how a Table field names a caption in that file

_ID = rf"(?:{'|'.join(PREFIXES)})-\d+"
HEADING = re.compile(rf"^### (?P<id>{_ID}) \[(?P<status>[{STATUSES}])\] (?P<name>.+?)\s*$")
FIELD = re.compile(r"^- (?P<key>[A-Z][A-Za-z ()]*): (?P<value>.*)$")
LINK = re.compile(rf"\[\[({_ID})\]\]")
TEST_NAME = re.compile(r"\btest_[a-z0-9_]+\b(?!\.py)")
COMMIT_HASH = re.compile(r"^[0-9a-f]{7,40}$")
SIMPLE_REPR_LIMIT = 400  # a constant whose repr is longer than this is data, not a value

INDEX_WORD_LIMIT = 3000  # words in kg/index.md, as len(text.split()); the check fails above it
INDEX_HEADER = """# Index

Every node on one line: ID, status and name, with the file for a constant.
`python kg_check.py --write-index` writes this file from the node files, and
the check fails when it differs from what that would write or when this file
passes 3,000 words. `README.md` is the legend. The table counts each file's
nodes and its words, len(text.split()) over the file.
"""


@dataclass
class Node:
    """One node of the graph: its heading, the section it sits in, and its fields as written."""

    id: str
    status: str
    name: str
    file: str  # the kg/ file the node is written in
    line: int
    section: str = ""  # the ## heading above the node, if any
    fields: dict[str, str] = field(default_factory=dict)
    field_lines: list[tuple[int, str, int]] = field(default_factory=list)  # (line, key, length)

    @property
    def path(self) -> str:
        """The file the index names for the node: its File field, else its kg/ file."""
        return self.fields.get("File", f"kg/{self.file}")

    @property
    def where(self) -> str:
        return f"kg/{self.file}:{self.line}: {self.id}"


def read_nodes(kg_dir: Path = KG_DIR) -> list[Node]:
    """Every node in the node files, in order."""
    nodes: list[Node] = []
    for name in NODE_FILES:
        node = None
        section = ""
        for number, line in enumerate((kg_dir / name).read_text().splitlines(), start=1):
            heading = HEADING.match(line)
            if heading:
                node = Node(
                    heading["id"], heading["status"], heading["name"], name, number, section
                )
                nodes.append(node)
            elif line.startswith("## "):
                node = None
                section = line[3:].strip()
            elif line.startswith("#"):
                node = None  # any other heading ends the node before it
            elif node is not None and (found := FIELD.match(line)):
                node.fields[found["key"]] = found["value"].strip()
                node.field_lines.append((number, found["key"], len(line)))
    return nodes


def problems(kg_dir: Path = KG_DIR, root: Path = ROOT) -> list[str]:
    """Everything that disagrees between the graph in kg_dir and the code under root."""
    _add_to_path(root)
    nodes = read_nodes(kg_dir)
    found: list[str] = []
    by_id: dict[str, Node] = {}
    for node in nodes:
        if node.id in by_id:
            found.append(f"{node.where} is defined twice")
        by_id[node.id] = node
    found += _dangling_links(kg_dir, by_id)
    found += _missing_modules(nodes, root)
    found += _bad_evidence(nodes)
    found += _unknown_tests(kg_dir, root)
    found += _wrong_constants(nodes, root)
    found += _bad_kinds(nodes)
    found += _unlisted_constants(nodes, root)
    found += _missing_functions(nodes)
    found += _missing_tables(nodes, root)
    found += _bad_fields(nodes)
    found += _ungrouped_decisions(nodes)
    found += _index_differs(kg_dir, nodes)
    found += _index_too_long(kg_dir)
    return found


def warnings(kg_dir: Path = KG_DIR, root: Path = ROOT) -> list[str]:
    """Source files whose import failed, so their constants went unchecked, and Commit fields
    that name a commit the git history does not hold. Information only: the history may be
    recreated, and the evidence is in the tests."""
    _add_to_path(root)
    for file in _source_files(root):
        _module(file)
    found = [
        f"{file}: not checked, its import failed ({why}); install the extra it needs"
        for file, why in sorted(_UNIMPORTABLE.items())
    ]
    if not (root / ".git").exists():
        return found
    checked: dict[str, bool] = {}
    for node in read_nodes(kg_dir):
        for token in _tokens(node.fields.get("Commit", "")):
            if not COMMIT_HASH.match(token):
                found.append(f"{node.where} names the commit {token!r}, which is not a hash")
                continue
            if token not in checked:
                checked[token] = _commit_exists(token, root)
            if not checked[token]:
                found.append(f"{node.where} names the commit {token}, which is not in the history")
    return found


def render_index(nodes: list[Node], kg_dir: Path = KG_DIR) -> str:
    """kg/index.md as it should read for these nodes: the header, the size table and the
    sections. The index's own row counts this file as written. A number is one word whatever
    its digits, so the count of a draft with a placeholder is the count of the final text."""
    body = _index_sections(nodes)
    draft = INDEX_HEADER + "\n" + "\n".join(_size_table(kg_dir, nodes, 0)) + "\n\n" + body
    table = _size_table(kg_dir, nodes, len(draft.split()))
    return INDEX_HEADER + "\n" + "\n".join(table) + "\n\n" + body


def _size_table(kg_dir: Path, nodes: list[Node], index_words: int) -> list[str]:
    """Each node file with its node count and word count, then the whole graph and the index."""
    rows = ["| File | Nodes | Words |", "| --- | ---: | ---: |"]
    total_nodes = total_words = 0
    for file in NODE_FILES:
        count = sum(1 for node in nodes if node.file == file)
        words = _words(kg_dir / file)
        total_nodes += count
        total_words += words
        rows.append(f"| {file} | {count} | {words:,} |")
    rows.append(f"| every node file | {total_nodes} | {total_words:,} |")
    rows.append(f"| index.md | | {index_words:,} |")
    return rows


def _words(path: Path) -> int:
    return len(path.read_text().split()) if path.exists() else 0


def _index_sections(nodes: list[Node]) -> str:
    """The node lines of the index, grouped by file."""
    lines = []
    for file, title in NODE_FILES.items():
        in_file = [node for node in nodes if node.file == file]
        lines += [f"## {title} (`{file}`)", ""]
        if file == "decisions.md":
            for group in DECISION_GROUPS:
                lines += [f"### {group}", ""]
                lines += [_index_line(node) for node in in_file if node.section == group]
                lines.append("")
        elif file == "rules.md":
            lines += [_index_line(node) for node in in_file if node.fields.get("Kind") != "label"]
            labels = [node.id for node in in_file if node.fields.get("Kind") == "label"]
            if labels:
                lines.append(f"- Labels: {', '.join(labels)}")
            lines.append("")
        else:
            lines += [_index_line(node) for node in in_file]
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def write_index(kg_dir: Path = KG_DIR) -> None:
    (kg_dir / "index.md").write_text(render_index(read_nodes(kg_dir), kg_dir))


def _index_line(node: Node) -> str:
    """ID, status and name; a constant also names its file, since the section does not."""
    line = f"- {node.id} [{node.status}] {node.name}"
    return line + (f" — {node.path}" if node.id.startswith("RUL-") else "")


def _add_to_path(root: Path) -> None:
    if str(root / "src") not in sys.path:
        sys.path.insert(0, str(root / "src"))


def _kg_lines(kg_dir: Path):
    """(file name, line number, line) for every line of every kg/ file."""
    for path in sorted(kg_dir.glob("*.md")):
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            yield path.name, number, line


def _tokens(text: str) -> list[str]:
    return [token.strip() for token in re.split(r"[,;]", text) if token.strip()]


def _dangling_links(kg_dir: Path, by_id: dict[str, Node]) -> list[str]:
    return [
        f"kg/{name}:{number}: [[{target}]] points to a node that does not exist"
        for name, number, line in _kg_lines(kg_dir)
        for target in LINK.findall(line)
        if target not in by_id
    ]


def _source_files(root: Path) -> list[str]:
    files = sorted((root / "src" / "hotel_market").glob("*.py")) + [root / "kg_check.py"]
    return [path.relative_to(root).as_posix() for path in files]


def _missing_modules(nodes: list[Node], root: Path) -> list[str]:
    covered = {node.fields.get("File") for node in nodes if node.id.startswith("MOD-")}
    return [f"{path} has no MOD node" for path in _source_files(root) if path not in covered]


def _bad_evidence(nodes: list[Node]) -> list[str]:
    """A [C] node cites tests and only tests, unless it is a policy node that a person reviewed. An
    [H] node links to the node that replaced, closed or moved it.
    """
    found = []
    for node in nodes:
        if node.status == "C":
            evidence = node.fields.get("Evidence", "")
            if evidence.strip() == REVIEW:
                if node.fields.get("Kind") != POLICY:
                    found.append(
                        f"{node.where} cites review as its evidence but is not a policy node "
                        f"(Kind: {POLICY})"
                    )
                continue
            cited = _tokens(evidence)
            if not cited:
                found.append(f"{node.where} is [C] but cites no test")
            found += [
                f"{node.where} cites {token!r}, which is not a test"
                for token in cited
                if not TEST_NAME.fullmatch(token)
            ]
        elif node.status == "H" and not any(
            LINK.search(node.fields.get(key, "")) for key in HISTORY_KEYS
        ):
            found.append(f"{node.where} is [H] but names no node that replaced it")
    return found


def _bad_fields(nodes: list[Node]) -> list[str]:
    """Every field line fits in FIELD_LIMIT characters. A node has at most FIELD_COUNT_LIMIT fields,
    so a node stays a few lines of plain facts.
    """
    found = []
    for node in nodes:
        found += [
            f"kg/{node.file}:{number}: {node.id}: the field {key} is {length} characters; "
            f"the limit is {FIELD_LIMIT}"
            for number, key, length in node.field_lines
            if length > FIELD_LIMIT
        ]
        if len(node.field_lines) > FIELD_COUNT_LIMIT:
            found.append(
                f"{node.where} has {len(node.field_lines)} fields; the limit is {FIELD_COUNT_LIMIT}"
            )
    return found


def _missing_tables(nodes: list[Node], root: Path) -> list[str]:
    """Every RES node names, in double quotes, the start of a caption line in docs/results.md."""
    path = root / RESULTS_FILE
    lines = path.read_text().splitlines() if path.exists() else []
    found = []
    for node in nodes:
        if not node.id.startswith("RES-"):
            continue
        captions = TABLE_CAPTION.findall(node.fields.get("Table", ""))
        if not captions:
            found.append(f"{node.where} names no table in {RESULTS_FILE}")
        found += [
            f'{node.where} names the table "{caption}", which is not in {RESULTS_FILE}'
            for caption in captions
            if not any(line.startswith(caption) for line in lines)
        ]
    return found


def _test_names(root: Path) -> set[str]:
    names = set()
    for path in (root / "tests").glob("test_*.py"):
        tree = ast.parse(path.read_text())
        names |= {
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        }
    return names


def _unknown_tests(kg_dir: Path, root: Path) -> list[str]:
    known = _test_names(root)
    return [
        f"kg/{name}:{number}: the cited test {cited} does not exist"
        for name, number, line in _kg_lines(kg_dir)
        for cited in TEST_NAME.findall(line)
        if cited not in known
    ]


def _commit_exists(commit: str, root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-e", f"{commit}^{{commit}}"],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:  # no git on this machine
        return True
    return result.returncode == 0


# A source file whose import failed, and why. Its constants are not checked, and warnings()
# says so once: the demo page needs the demo extra, which the dev install does not bring.
_UNIMPORTABLE: dict[str, str] = {}


def _module(file: str) -> object | None:
    path = Path(file)
    if path.parts[:2] != ("src", "hotel_market") or path.suffix != ".py":
        return None
    try:
        return importlib.import_module(f"hotel_market.{path.stem}")
    except ImportError as error:
        _UNIMPORTABLE[file] = str(error)
        return None


def _constant_nodes(nodes: list[Node]) -> list[Node]:
    """The RUL nodes that describe a constant still in the code: those that name a file
    and are not historical."""
    return [
        node
        for node in nodes
        if node.id.startswith("RUL-") and "File" in node.fields and node.status != "H"
    ]


def _wrong_constants(nodes: list[Node], root: Path) -> list[str]:
    found = []
    for node in _constant_nodes(nodes):
        file = node.fields["File"]
        if file.endswith(".toml"):
            defined, actual = _setting(root / file, node.fields.get("Key", ""))
        else:
            module = _module(file)
            if file in _UNIMPORTABLE:
                continue  # not checked; warnings() names the file
            defined = module is not None and hasattr(module, node.name)
            actual = getattr(module, node.name, None)
        if not defined:
            found.append(f"{node.where}: {node.name} is not defined in {file}")
            continue
        if "Value" not in node.fields:
            continue
        try:
            written = _evaluate(node.fields["Value"])
        except ValueError as error:
            found.append(f"{node.where}: {error}")
            continue
        if written != actual:
            found.append(
                f"{node.where}: {node.name} is {node.fields['Value']} in kg/rules.md "
                f"but {actual!r} in {file}"
            )
    return found


def _setting(path: Path, key: str) -> tuple[bool, object]:
    """(whether the dotted key exists in the TOML file, its value)."""
    if not path.exists() or not key:
        return False, None
    value = tomllib.loads(path.read_text())
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    if isinstance(value, list):
        value = tuple(value)
    return True, value


def _settings(path: Path) -> list[tuple[str, object]]:
    """(dotted key, value) for every setting in the customer file outside the hotels."""
    found = []

    def walk(table: dict, prefix: str) -> None:
        for key, value in table.items():
            if key == "hotels":
                continue  # the hotels are data, described by their DAT node
            if isinstance(value, dict):
                walk(value, f"{prefix}{key}.")
            else:
                found.append((f"{prefix}{key}", tuple(value) if isinstance(value, list) else value))

    if path.exists():
        walk(tomllib.loads(path.read_text()), "")
    return found


def _bad_kinds(nodes: list[Node]) -> list[str]:
    return [
        f"{node.where}: {node.name} has Kind {node.fields.get('Kind')!r}; "
        f"a constant is a parameter or a label"
        for node in _constant_nodes(nodes)
        if node.fields.get("Kind") not in KINDS
    ]


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def _evaluate(text: str):
    """The value of a constant as kg/rules.md writes it. It is a Python literal, arithmetic on
    literals such as 1 / 3, or date(year, month, day).
    """
    try:
        tree = ast.parse(text.strip(), mode="eval")
    except SyntaxError:
        raise ValueError(f"cannot read the value {text!r}") from None
    return _value(tree.body)


def _value(node: ast.expr):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Tuple):
        return tuple(_value(element) for element in node.elts)
    if isinstance(node, ast.List):
        return [_value(element) for element in node.elts]
    if isinstance(node, ast.Set):
        return {_value(element) for element in node.elts}
    if isinstance(node, ast.Dict):
        return {_value(key): _value(value) for key, value in zip(node.keys, node.values)}
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_value(node.operand)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_value(node.left), _value(node.right))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "date":
        return date(*(_value(argument) for argument in node.args))
    raise ValueError(f"cannot read the value {ast.unparse(node)!r}")


def _is_simple(value) -> bool:
    """A value that belongs in kg/rules.md: numbers, strings, dates and small containers of them."""
    if isinstance(value, (bool, int, float, str, date, type(None))):
        return len(repr(value)) <= SIMPLE_REPR_LIMIT
    if isinstance(value, (tuple, list, set, frozenset)):
        return all(_is_simple(item) for item in value) and len(repr(value)) <= SIMPLE_REPR_LIMIT
    if isinstance(value, dict):
        items = list(value.keys()) + list(value.values())
        return all(_is_simple(item) for item in items) and len(repr(value)) <= SIMPLE_REPR_LIMIT
    return False


def _code_constants(root: Path) -> list[tuple[str, str, object]]:
    """(file, name, value) for every public UPPER_CASE constant assigned at module level."""
    constants = []
    for path in sorted((root / "src" / "hotel_market").glob("*.py")):
        names = []
        for statement in ast.parse(path.read_text()).body:
            if not isinstance(statement, ast.Assign):
                continue
            for target in statement.targets:
                elements = target.elts if isinstance(target, ast.Tuple) else [target]
                names += [
                    element.id
                    for element in elements
                    if isinstance(element, ast.Name)
                    and element.id.isupper()
                    and not element.id.startswith("_")
                ]
        if not names:
            continue
        file = path.relative_to(root).as_posix()
        module = _module(file)
        if module is None:
            continue  # its import failed; warnings() names the file
        for name in names:
            value = getattr(module, name)
            if _is_simple(value):
                constants.append((file, name, value))
    return constants


def _unlisted_constants(nodes: list[Node], root: Path) -> list[str]:
    listed = {(node.fields["File"], node.name) for node in _constant_nodes(nodes)}
    keyed = {
        (node.fields["File"], node.fields.get("Key"))
        for node in _constant_nodes(nodes)
        if node.fields["File"].endswith(".toml")
    }
    found = [
        f"{file}: {name} = {value!r} has no RUL node in kg/rules.md"
        for file, name, value in _code_constants(root)
        if (file, name) not in listed
    ]
    found += [
        f"{CUSTOMER_FILE}: {key} = {value!r} has no RUL node in kg/rules.md"
        for key, value in _settings(root / CUSTOMER_FILE)
        if (CUSTOMER_FILE, key) not in keyed
    ]
    return found


def _missing_functions(nodes: list[Node]) -> list[str]:
    """Every MEA node names the function that computes it, and that function exists."""
    found = []
    for node in nodes:
        if not node.id.startswith("MEA-"):
            continue
        dotted = node.fields.get("Function", "")
        if not dotted:
            found.append(f"{node.where} names no Function")
        elif not _resolves(dotted):
            found.append(f"{node.where}: the function {dotted} does not exist")
    return found


def _resolves(dotted: str) -> bool:
    """Whether module.attribute[.attribute...] names something callable."""
    parts = dotted.split(".")
    for split in range(len(parts) - 1, 0, -1):
        try:
            target = importlib.import_module(".".join(parts[:split]))
        except ImportError:
            continue
        for attribute in parts[split:]:
            target = getattr(target, attribute, None)
            if target is None:
                return False
        return callable(target)
    return False


def _ungrouped_decisions(nodes: list[Node]) -> list[str]:
    return [
        f"{node.where} is under {node.section!r}; a decision sits under one of "
        f"{' or '.join(repr(group) for group in DECISION_GROUPS)}"
        for node in nodes
        if node.id.startswith("DEC-") and node.section not in DECISION_GROUPS
    ]


def _index_differs(kg_dir: Path, nodes: list[Node]) -> list[str]:
    path = kg_dir / "index.md"
    on_disk = path.read_text() if path.exists() else ""
    if on_disk == render_index(nodes, kg_dir):
        return []
    return ["kg/index.md differs from the generated index; run python kg_check.py --write-index"]


def _index_too_long(kg_dir: Path) -> list[str]:
    words = _words(kg_dir / "index.md")
    if words <= INDEX_WORD_LIMIT:
        return []
    return [f"kg/index.md has {words:,} words; the limit is {INDEX_WORD_LIMIT:,}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the knowledge graph against the code.")
    parser.add_argument(
        "--write-index", action="store_true", help="rewrite kg/index.md from the node files first"
    )
    if parser.parse_args(argv).write_index:
        write_index()
        print("wrote kg/index.md")
    for warning in warnings():
        print(f"warning: {warning}")
    found = problems()
    for problem in found:
        print(problem)
    print(f"{len(found)} problem(s)" if found else "kg/ agrees with the code")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
