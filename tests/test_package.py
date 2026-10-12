"""The package as installed. It imports, and python -m runs the command. The repository is laid out
and configured the way the decisions in kg/ say."""

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


def test_the_image_takes_its_python_version_as_a_build_argument():
    # The Dockerfile builds on python:<PYTHON>-slim with 3.12 as the default, and the
    # Makefile tags the image by that version, so one image per Python can sit side by side.
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "ARG PYTHON=3.12\n" in dockerfile and "FROM python:${PYTHON}-slim" in dockerfile
    makefile = (ROOT / "Makefile").read_text()
    assert "--build-arg PYTHON=$(IMAGE_PYTHON)" in makefile
    assert "TAG    := $(IMAGE):py$(IMAGE_PYTHON)" in makefile
    assert "IMAGE_PYTHON := $(if $(filter 3.%,$(PYTHON)),$(PYTHON),3.12)" in makefile
