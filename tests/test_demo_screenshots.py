"""scripts/demo_screenshots.py: the page at 1440 by 900, measured on every hotel and seven days,
six pages screenshot."""

import importlib.util
from pathlib import Path

import duckdb
import pytest

from hotel_market.customer import demo

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
    assert screenshots.STATES == (("off", ""), ("on", "&end=1"))
    assert (screenshots.WIDTH, screenshots.HEIGHT) == (1440, 900)
    # Every hotel of the demo market is measured on seven days, and only the six pages are saved.
    assert screenshots.HOTELS == tuple(hotel.key for hotel in demo().hotels)
    assert screenshots.DAYS == (10, 18, 20, 23, 30, 34, 40)
    assert set(screenshots.PAGES) < set(
        (hotel, day) for hotel in screenshots.HOTELS for day in screenshots.DAYS
    )
    # On a finer clock the pages are every hotel on four days at every tick, in both states.
    daily = screenshots.pages()
    assert len(daily) == 4 * 7 * 2 and daily[0] == ("convention", 10, 1, "off", "")
    assert daily[1] == ("convention", 10, 1, "on", "&end=1")
    intraday = screenshots.pages(4)
    assert screenshots.INTRADAY_DAYS == (20, 25, 30, 45) and len(intraday) == 4 * 4 * 4 * 2
    assert intraday[0] == ("convention", 20, 1, "off", "&tick=1")
    assert intraday[1] == ("convention", 20, 1, "on", "&tick=1&end=1")
    assert intraday[-1] == ("airport", 45, 4, "on", "&tick=4&end=1")


def test_every_checked_page_fits_the_window_and_six_are_saved(screenshots, demo_file, tmp_path):
    # Needs a Chromium-based browser and the demo extra; skipped without them.
    pytest.importorskip("streamlit")
    browser = screenshots.find_browser()
    if browser is None:
        pytest.skip("no Chromium-based browser found")
    results = screenshots.shoot(demo_file, tmp_path / "shots", browser)
    assert [(hotel, day, tick, state) for hotel, day, tick, state, _, _ in results] == [
        (hotel, day, 1, state)
        for hotel in screenshots.HOTELS
        for day in screenshots.DAYS
        for state, _ in screenshots.STATES
    ]
    assert results[0][5].name == "convention-day10.png"
    assert results[1][5].name == "convention-day10-end.png"
    for hotel, day, _, state, measured, path in results:
        if (hotel, day) in screenshots.PAGES:
            assert path.exists() and path.stat().st_size > 10_000
        else:
            assert path is None
        # The strip's four tiles, then five a row of the scorecard: two rows, or four with the
        # five months on.
        assert measured["window"] == 900 and measured["metrics"] == (23 if state == "on" else 13)
        assert not screenshots.too_tall(measured), (hotel, day, state, measured)
    assert sorted(file.name for file in (tmp_path / "shots").iterdir()) == [
        "airport-day20-end.png",
        "airport-day20.png",
        "convention-day10-end.png",
        "convention-day10.png",
        "full-service-day30-end.png",
        "full-service-day30.png",
        screenshots.SERVER_LOG,
    ]


def test_a_page_that_does_not_render_prints_the_servers_log(screenshots, tmp_path, capsys):
    # A file with no tables makes the page fail. Needs a browser; skipped without one.
    pytest.importorskip("streamlit")
    browser = screenshots.find_browser()
    if browser is None:
        pytest.skip("no Chromium-based browser found")
    empty = tmp_path / "empty.duckdb"
    duckdb.connect(str(empty)).close()
    with pytest.raises(TimeoutError):
        screenshots.shoot(empty, tmp_path / "shots", browser, timeout=15)
    out = capsys.readouterr().out
    assert "did not render" in out and "server.log" in out and "hotels" in out
    assert (tmp_path / "shots" / screenshots.SERVER_LOG).exists()


def test_the_intraday_pages_fit_the_window_at_every_tick_and_nothing_is_saved(
    screenshots, demo_file_intraday, tmp_path
):
    # The lifestyle hotel's day 25 at each of four ticks, in both states, stands in for the
    # script's full intraday check, which make screenshots runs. Needs a browser; skipped
    # without one.
    pytest.importorskip("streamlit")
    browser = screenshots.find_browser()
    if browser is None:
        pytest.skip("no Chromium-based browser found")
    results = screenshots.shoot(
        demo_file_intraday, tmp_path / "shots", browser, ticks=4, wanted=[("lifestyle", 25)]
    )
    assert [(tick, state) for _, _, tick, state, _, _ in results] == [
        (tick, state) for tick in (1, 2, 3, 4) for state, _ in screenshots.STATES
    ]
    for hotel, day, tick, state, measured, path in results:
        assert (hotel, day) == ("lifestyle", 25) and path is None
        assert measured["window"] == 900 and measured["metrics"] == (23 if state == "on" else 13)
        assert not screenshots.too_tall(measured), (tick, state, measured)
    assert [file.name for file in (tmp_path / "shots").iterdir()] == [screenshots.SERVER_LOG]
