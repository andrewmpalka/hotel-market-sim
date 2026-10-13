"""scripts/demo_screenshots.py: the page at 1440 by 900, screenshot and measured."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def screenshots():
    spec = importlib.util.spec_from_file_location(
        "demo_screenshots", ROOT / "scripts" / "demo_screenshots.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_browser_is_the_named_one_or_the_first_found(screenshots, tmp_path):
    named = tmp_path / "my-chromium"
    named.write_text("")
    assert screenshots.find_browser({"HOTEL_MARKET_BROWSER": str(named)}) == str(named)
    assert screenshots.find_browser({"HOTEL_MARKET_BROWSER": str(tmp_path / "none")}) is None
    assert screenshots.BROWSERS[0].endswith("Chromium.app/Contents/MacOS/Chromium")
    found = screenshots.find_browser({})
    assert found is None or Path(found).exists()


def test_a_page_is_too_tall_when_its_content_passes_the_window_or_it_scrolls(screenshots):
    fits = {"window": 900, "content": 860, "scroll": 900, "visible": 900}
    assert not screenshots.too_tall(fits)
    assert screenshots.too_tall({**fits, "content": 901})
    assert screenshots.too_tall({**fits, "scroll": 901})
    assert screenshots.PAGES == (("convention", 10), ("airport", 20), ("full-service", 30))
    assert (screenshots.WIDTH, screenshots.HEIGHT) == (1440, 900)


def test_the_three_pages_fit_the_window(screenshots, demo_file, tmp_path):
    # Needs a Chromium-based browser and the demo extra; skipped without them.
    pytest.importorskip("streamlit")
    browser = screenshots.find_browser()
    if browser is None:
        pytest.skip("no Chromium-based browser found")
    results = screenshots.shoot(demo_file, tmp_path / "shots", browser)
    assert [(hotel, day) for hotel, day, _, _ in results] == list(screenshots.PAGES)
    for hotel, day, measured, path in results:
        assert path.exists() and path.stat().st_size > 10_000
        assert measured["window"] == 900 and measured["metrics"] == 20
        assert not screenshots.too_tall(measured), (hotel, day, measured)
