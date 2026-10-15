"""The knowledge graph in kg/ agrees with the code, and kg_check.py notices when it does not."""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_kg_check():
    """kg_check.py as a module: it lives at the repository root, outside the package."""
    spec = importlib.util.spec_from_file_location("kg_check", ROOT / "kg_check.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve the annotations through sys.modules
    spec.loader.exec_module(module)
    return module


kg_check = _load_kg_check()


def test_the_knowledge_graph_agrees_with_the_code():
    assert kg_check.problems() == []


def test_the_index_on_disk_is_the_generated_one():
    assert (ROOT / "kg" / "index.md").read_text() == kg_check.render_index(kg_check.read_nodes())


@pytest.fixture
def kg_copy(tmp_path):
    """A copy of kg/ to break on purpose."""
    shutil.copytree(ROOT / "kg", tmp_path / "kg")
    return tmp_path / "kg"


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new, 1))


def _reported(kg_copy: Path, text: str) -> bool:
    return any(text in problem for problem in kg_check.problems(kg_copy))


def test_a_link_to_a_node_that_does_not_exist_is_reported(kg_copy):
    forks = kg_copy / "forks.md"
    forks.write_text(forks.read_text() + "\nSee [[DEC-999]].\n")
    assert _reported(kg_copy, "[[DEC-999]] points to a node that does not exist")


def test_a_source_file_without_a_mod_node_is_reported(kg_copy):
    _replace(
        kg_copy / "modules.md",
        "- File: src/hotel_market/text.py",
        "- File: src/hotel_market/texts.py",
    )
    assert _reported(kg_copy, "src/hotel_market/text.py has no MOD node")


def test_a_confirmed_node_without_evidence_is_reported(kg_copy):
    _replace(kg_copy / "shocks.md", "- Evidence:", "- Evidence was:")
    assert _reported(kg_copy, "SHK-01 is [C] but cites no test")


def test_a_confirmed_node_whose_evidence_is_a_commit_is_reported(kg_copy):
    _replace(kg_copy / "shocks.md", "- Evidence: test_", "- Evidence: 1d75b2e, test_")
    assert _reported(kg_copy, "SHK-01 cites '1d75b2e', which is not a test")


def test_a_cited_test_that_does_not_exist_is_reported(kg_copy):
    _replace(
        kg_copy / "shocks.md",
        "test_each_shock_flags_on_the_day_it_becomes_known",
        "test_each_shock_flags_on_the_day_it_became_known",
    )
    assert _reported(kg_copy, "test_each_shock_flags_on_the_day_it_became_known does not exist")


def test_a_historical_node_without_its_replacement_is_reported(kg_copy):
    _replace(
        kg_copy / "decisions.md", "- Replaced by: [[DEC-09]]", "- Replaced by: a computed night"
    )
    assert _reported(kg_copy, "DEC-08 is [H] but names no node that replaced it")


def test_a_constant_whose_value_differs_from_the_code_is_reported(kg_copy):
    _replace(
        kg_copy / "rules.md",
        "- Value: 1.5\n- File: src/hotel_market/bookings.py",
        "- Value: 1.6\n- File: src/hotel_market/bookings.py",
    )
    assert _reported(
        kg_copy, "ELASTICITY is 1.6 in kg/rules.md but 1.5 in src/hotel_market/bookings.py"
    )


def test_a_constant_without_a_kind_is_reported(kg_copy):
    _replace(
        kg_copy / "rules.md",
        "- File: src/hotel_market/bookings.py\n- Kind: parameter",
        "- File: src/hotel_market/bookings.py\n- Kind: number",
    )
    assert _reported(kg_copy, "ELASTICITY has Kind 'number'; a constant is a parameter or a label")


def test_a_constant_missing_from_the_graph_is_reported(kg_copy):
    _replace(
        kg_copy / "rules.md", "### RUL-54 [C] BAND_STANDARD_ERRORS", "### RUL-54 [C] BAND_WIDTH"
    )
    assert _reported(kg_copy, "BAND_STANDARD_ERRORS = 1 has no RUL node")


def test_a_customer_setting_missing_from_the_graph_is_reported(kg_copy):
    _replace(kg_copy / "rules.md", "- Key: detect.hold_days\n", "- Key: detect.hold_days_was\n")
    assert _reported(kg_copy, "customers/demo.toml: detect.hold_days = 7 has no RUL node")


def test_a_key_with_a_star_reads_every_hotels_setting_and_a_missing_one_is_undefined():
    path = ROOT / "customers" / "demo.toml"
    assert kg_check._setting(path, "hotels[*].rooms") == (True, (400, 250, 120, 150))
    assert kg_check._setting(path, "hotels[*].booking_curve.days_out")[1][0] == (0, 7, 30, 60, 90)
    assert kg_check._setting(path, "hotels[*].rooms_was") == (False, None)
    assert kg_check._setting(path, "limits[*].floor_share") == (False, None)
    assert kg_check._setting(path, "detect.hold_days") == (True, 7)


def test_a_shock_in_the_code_without_a_node_is_reported(monkeypatch):
    """A second event added to shocks.py has no SHK node, so the check fails until a node names
    its file and its known day. The shipped shocks all have one."""
    from dataclasses import replace

    from hotel_market import shocks

    assert not any("has no SHK node" in problem for problem in kg_check.problems())
    second = replace(shocks.EVENTS[0], name="Trade fair", known_day=25, start_day=70, end_day=72)
    monkeypatch.setattr(shocks, "EVENTS", shocks.EVENTS + [second])
    assert any(
        "src/hotel_market/shocks.py: the event 'Trade fair' known on day 25 has no SHK node "
        "naming that day" in problem
        for problem in kg_check.problems()
    )


def test_a_measure_whose_function_does_not_exist_is_reported(kg_copy):
    _replace(
        kg_copy / "measures.md",
        "- Function: hotel_market.bookings.Books.revpar",
        "- Function: hotel_market.bookings.Books.revpar_per_night",
    )
    assert _reported(
        kg_copy, "the function hotel_market.bookings.Books.revpar_per_night does not exist"
    )


def test_a_decision_outside_the_two_groups_is_reported(kg_copy):
    _replace(kg_copy / "decisions.md", "## Engineering", "## Plumbing")
    assert _reported(kg_copy, "DEC-23 is under 'Plumbing'")


def test_an_index_that_differs_from_the_generated_one_is_reported_and_write_index_fixes_it(kg_copy):
    _replace(kg_copy / "index.md", "- SHK-01 [C]", "- SHK-01 [O]")
    assert _reported(kg_copy, "kg/index.md differs from the generated index")
    kg_check.write_index(kg_copy)
    assert kg_check.problems(kg_copy) == []


def test_a_commit_missing_from_the_history_is_a_warning_not_a_problem(kg_copy):
    if not (ROOT / ".git").exists():
        pytest.skip("no git history to look the commit up in")
    _replace(kg_copy / "decisions.md", "- Commit: 15e0215", "- Commit: 0000000")
    assert not any("0000000" in problem for problem in kg_check.problems(kg_copy))
    assert any(
        "DEC-01 names the commit 0000000, which is not in the history" in warning
        for warning in kg_check.warnings(kg_copy)
    )


def _set_field(path: Path, node_id: str, key: str, value: str | None) -> None:
    """Replace, add or, with None, remove one field of a node in a kg/ copy."""
    lines = path.read_text().splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith(f"### {node_id} "))
    end = start + 1
    while end < len(lines) and lines[end].startswith("- "):
        end += 1
    kept = [line for line in lines[start + 1 : end] if not line.startswith(f"- {key}: ")]
    if value is not None:
        kept.append(f"- {key}: {value}\n")
    path.write_text("".join(lines[: start + 1] + kept + lines[end:]))


def _problem_with(kg_copy: Path, *texts: str) -> bool:
    return any(all(text in problem for text in texts) for problem in kg_check.problems(kg_copy))


def test_a_field_longer_than_the_limit_is_reported(kg_copy):
    _set_field(kg_copy / "shocks.md", "SHK-01", "Known on day", "10, " + "and more " * 30)
    assert _problem_with(kg_copy, "SHK-01: the field Known on day is", "the limit is 240")


def test_a_node_with_more_than_eight_fields_is_reported(kg_copy):
    for extra in ("one", "two", "three", "four", "five", "six", "seven", "eight"):
        _set_field(kg_copy / "shocks.md", "SHK-01", f"Extra {extra}", "a fact")
    assert _problem_with(kg_copy, "SHK-01 has", "fields; the limit is 8")


def test_review_as_evidence_is_accepted_only_on_a_policy_node(kg_copy):
    _set_field(kg_copy / "shocks.md", "SHK-01", "Evidence", "review")
    assert _problem_with(kg_copy, "SHK-01 cites review as its evidence but is not a policy node")
    _set_field(kg_copy / "shocks.md", "SHK-01", "Kind", "policy")
    assert not _problem_with(kg_copy, "SHK-01 cites review")


def test_a_results_node_names_a_table_that_is_in_docs_results_md(kg_copy):
    results = kg_copy / "results.md"
    _set_field(results, "RES-01", "Table", 'docs/results.md, "A table that is not there"')
    assert _problem_with(
        kg_copy, 'RES-01 names the table "A table that is not there"', "not in docs/results.md"
    )
    _set_field(results, "RES-01", "Table", None)
    assert _problem_with(kg_copy, "RES-01 names no table in docs/results.md")


def test_a_closed_fork_names_what_closed_it(kg_copy):
    forks = kg_copy / "forks.md"
    _set_field(forks, "FRK-01", "Replaced by", None)
    _set_field(forks, "FRK-01", "Closed by", "[[DEC-41]]")
    assert not _problem_with(kg_copy, "FRK-01 is [H]")
    _set_field(forks, "FRK-01", "Closed by", "the customer file")
    assert _problem_with(kg_copy, "FRK-01 is [H] but names no node that replaced it")


def test_a_module_that_cannot_import_is_skipped_with_a_warning():
    """Without the demo extra the demo page cannot import. The checker then skips that file's
    constants, warns once, and still passes, so the dev install and the container can run it."""
    code = (
        "import sys; sys.modules['streamlit'] = None; sys.modules['altair'] = None\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "import kg_check\n"
        "print(len(kg_check.problems()))\n"
        "print('\\n'.join(kg_check.warnings()))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(ROOT)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=True,
    )
    lines = result.stdout.splitlines()
    assert lines[0] == "0", result.stdout
    assert any("demo_page.py: not checked" in line for line in lines[1:]), result.stdout


def test_the_index_counts_each_files_words_and_a_long_index_is_reported(kg_copy):
    """The index opens with each file's node and word counts and its own, as len(text.split())
    over the file, and the check holds the index under its word limit."""
    index = (ROOT / "kg" / "index.md").read_text()
    nodes = kg_check.read_nodes()
    for file in kg_check.NODE_FILES:
        words = len((ROOT / "kg" / file).read_text().split())
        count = sum(1 for node in nodes if node.file == file)
        assert f"| {file} | {count} | {words:,} |" in index
    assert f"| index.md | | {len(index.split()):,} |" in index
    assert len(index.split()) <= kg_check.INDEX_WORD_LIMIT
    # A stale count differs from the generated index, and a long index is reported as such.
    _replace(kg_copy / "index.md", "| index.md | |", "| index.md | | 1 |")
    assert _reported(kg_copy, "kg/index.md differs from the generated index")
    padded = kg_check.render_index(kg_check.read_nodes(kg_copy), kg_copy) + "word " * 3001
    (kg_copy / "index.md").write_text(padded)
    assert _problem_with(kg_copy, "kg/index.md has", "words; the limit is 3,000")
