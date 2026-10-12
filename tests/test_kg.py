"""The knowledge graph in kg/ agrees with the code, and kg_check.py notices when it does not."""

import importlib.util
import shutil
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
