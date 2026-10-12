"""The package as installed: it imports, python -m runs the command, and the
repository is laid out and configured the way the decisions in kg/ say."""

import subprocess
import sys
import tomllib
from pathlib import Path

import hotel_market

ROOT = Path(__file__).resolve().parents[1]


def test_the_package_imports_and_describes_the_project():
    assert "hotel market" in hotel_market.__doc__.lower()
    assert "synthetic" in hotel_market.__doc__.lower()


def test_python_m_hotel_market_runs_the_command():
    result = subprocess.run(
        [sys.executable, "-m", "hotel_market", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "--seed" in result.stdout and "--replay" in result.stdout


def test_the_formatter_runs_at_100_columns():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert pyproject["tool"]["ruff"]["line-length"] == 100
    assert "ruff" in pyproject["project"]["optional-dependencies"]["dev"]


def test_the_checks_run_locally_with_no_hosted_workflow():
    assert not (ROOT / ".github").exists()
    makefile = (ROOT / "Makefile").read_text()
    assert "\ntest:" in makefile and "\nlint:" in makefile and "\ntest-all:" in makefile
    assert "--slow" in (ROOT / "tests" / "conftest.py").read_text()
