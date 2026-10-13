"""Module 27, demo_page.py: the read-only page. It imports nothing from the package and does no
arithmetic on a figure; every figure it shows is a row code wrote."""

import ast
from pathlib import Path

import pytest

PAGE = Path(__file__).resolve().parents[1] / "src" / "hotel_market" / "demo_page.py"
ARITHMETIC = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.MatMult)
# Builtins and frame methods that make a figure from figures.
FIGURE_FUNCTIONS = {
    "sum", "round", "abs", "min", "max", "divmod", "pow", "mean", "median", "cumsum", "diff",
    "pct_change", "add", "sub", "mul", "div", "truediv", "agg", "aggregate", "prod", "quantile",
}  # fmt: skip
ALLOWED_IMPORTS = {"os", "pathlib", "altair", "duckdb", "streamlit"}


def _tree() -> ast.Module:
    return ast.parse(PAGE.read_text())


def test_the_page_imports_nothing_from_the_package_or_the_simulator():
    imported = set()
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert not any(name.startswith("hotel_market") for name in imported), imported
    assert imported <= ALLOWED_IMPORTS, imported


def test_the_page_does_no_arithmetic_on_a_figure():
    for node in ast.walk(_tree()):
        if isinstance(node, ast.BinOp):
            assert not isinstance(node.op, ARITHMETIC), ast.unparse(node)
        assert not isinstance(node, ast.AugAssign), ast.unparse(node)
        if isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            assert name not in FIGURE_FUNCTIONS, ast.unparse(node)


def test_the_page_shows_the_convention_hotel_on_day_10(demo_file, monkeypatch):
    testing = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("HOTEL_MARKET_DEMO_FILE", str(demo_file))
    page = testing.AppTest.from_file(str(PAGE), default_timeout=60)
    page.run()
    assert not page.exception
    page.sidebar.selectbox[0].select("Downtown convention hotel")
    page.sidebar.slider[0].set_value(10)
    page.run()
    assert not page.exception
    assert page.subheader[0].value == "Downtown convention hotel, day 10"
    text = "\n".join(block.value for block in page.markdown)
    assert "An event, the convention, was announced for stay dates 45 to 48." in text
    assert "The comp set median is up 15.0% for stay dates 45 to 48." in text
    assert (
        "**Accepted:** raise 5% on Fri; raise 10% on Thu, Sat for stay dates 45 to 48, "
        "$8,050 more than holding. A convention has been announced"
    ) in text
    assert [metric.label for metric in page.metric] == [
        "Occupancy", "ADR", "RevPAR", "Room revenue", "Contribution"
    ]  # fmt: skip
    assert page.metric[1].value == "$220.00" and page.metric[1].delta == "+0.00"
    assert page.expander[0].label == "Held flags: 0"
