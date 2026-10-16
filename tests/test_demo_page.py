"""Module 27, demo_page.py: the read-only page. It imports nothing from the package and does no
arithmetic on a figure; every figure it shows is a row code wrote."""

import ast
import json
import shutil
from pathlib import Path

import pytest

from hotel_market import stored

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "src" / "hotel_market" / "demo_page.py"
ARITHMETIC = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.MatMult)
# Builtins and frame methods that make a figure from figures.
FIGURE_FUNCTIONS = {
    "sum", "round", "abs", "min", "max", "divmod", "pow", "mean", "median", "cumsum", "diff",
    "pct_change", "add", "sub", "mul", "div", "truediv", "agg", "aggregate", "prod", "quantile",
}  # fmt: skip
ALLOWED_IMPORTS = {"os", "pathlib", "altair", "duckdb", "streamlit"}
AIRPORT_DAY_20 = (  # the plan line, then the recorded run's reason, its dollar signs escaped
    "**Accepted:** raise 5% on Tue, Fri; raise 10% on Mon, Wed, Thu, Sun for Tue 23 Feb [50] to "
    "Fri 23 Apr [109], \\$10,140 more than holding. "
    + json.loads((ROOT / "tests" / "fixtures" / "live_seed7" / "day020_airport.json").read_text())[
        "decisions"
    ][0]["reason"].replace("$", "\\$")
)
SIDEBAR = (  # the run table's words: the recorded live run covers every request of seed 7
    "Seed 7 of the simulated market. The reasons are the model's, from the recorded live run. "
    "The page reads a file code wrote and computes nothing."
)


def _tree() -> ast.Module:
    return ast.parse(PAGE.read_text())


def _page(testing, monkeypatch, file, hotel=None, day=None, end=False):
    """The page run on the file, opened at the hotel and day the query string names, with the
    end-of-run result turned on by the query string when asked."""
    monkeypatch.setenv("HOTEL_MARKET_DEMO_FILE", str(file))
    page = testing.AppTest.from_file(str(PAGE), default_timeout=60)
    if hotel is not None:
        page.query_params["hotel"] = hotel
    if day is not None:
        page.query_params["day"] = str(day)
    if end:
        page.query_params["end"] = "1"
    page.run()
    assert not page.exception
    return page


def _text(page) -> str:
    return "\n".join(block.value for block in page.markdown)


def _rate_chart_spec(page) -> str:
    """The rate chart's Vega-Lite spec, the first chart on the page."""
    return page.get("vega_lite_chart")[0].proto.spec


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


def test_the_page_shows_the_airport_hotel_on_day_20(demo_file, monkeypatch):
    testing = pytest.importorskip("streamlit.testing.v1")
    page = _page(testing, monkeypatch, demo_file)
    assert page.subheader[0].value == "Downtown convention hotel, Mon 4 Jan 2027 [day 0]"
    assert '"planned_rate"' not in _rate_chart_spec(page)  # no accepted plan, no legend entry
    page.sidebar.selectbox[0].select("Airport hotel")
    page.sidebar.slider[0].set_value(20)
    page.run()
    assert not page.exception
    assert page.subheader[0].value == "Airport hotel, Sun 24 Jan 2027 [day 20]"
    text = _text(page)
    assert (
        "The airlines filed a schedule change: arriving passengers are up 12.8% to 23.0% for "
        "Tue 23 Feb [50] to Wed 2 Jun [149]."
    ) in text
    assert "**Stay dates ahead, Sun 24 Jan [20] to Fri 23 Apr [109].**" in text
    assert AIRPORT_DAY_20 in text
    assert "No flag was held today." in text and not page.expander
    assert "Since the last change" not in text  # the airport's request listed no earlier change
    # The accepted plan's rate is a dashed line in its own colour, with a legend entry.
    spec = _rate_chart_spec(page)
    assert '"planned_rate"' in spec and "#1baf7a" in spec and "#2a78d6" in spec
    # The scorecard: the nights already stayed for the hotel and for all four, each labelled;
    # five tiles each, and a zero change written "0" (no arrow). The end-of-run result is off.
    stayed = [
        "Airport hotel: nights already stayed, Mon 4 Jan [0] to Sat 23 Jan [19]",
        "All four hotels: nights already stayed, Mon 4 Jan [0] to Sat 23 Jan [19]",
    ]
    assert [caption.value for caption in page.main.caption] == stayed
    labels = ["Occupancy", "ADR", "RevPAR", "Room revenue", "Contribution"]
    assert [metric.label for metric in page.metric] == labels * 2
    assert page.metric[1].value == "$140.00" and page.metric[1].delta == "0"
    assert not page.sidebar.checkbox[0].value and len(page.get("vega_lite_chart")) == 2
    # The sidebar reads the seed and the reasons' source from the file, and defines contribution.
    assert [caption.value for caption in page.sidebar.caption] == [
        SIDEBAR,
        "Contribution is room revenue minus the cost of servicing every room sold.",
    ]
    # The checkbox adds the complete result for both scopes and the contribution line.
    page.sidebar.checkbox[0].check()
    page.run()
    assert not page.exception
    assert [caption.value for caption in page.main.caption] == [
        stayed[0],
        "Airport hotel: once every stay date is complete, Mon 4 Jan [0] to Wed 2 Jun [149]",
        stayed[1],
        "All four hotels: once every stay date is complete, Mon 4 Jan [0] to Wed 2 Jun [149]",
        "Contribution difference by stay date, once every stay date is complete",
    ]
    assert [metric.label for metric in page.metric] == labels * 4
    assert page.metric[9].value == "$1,879,045" and page.metric[9].delta == "+$6,125"
    assert page.metric[19].value == "$14,505,130" and page.metric[19].delta == "+$19,796"
    assert len(page.get("vega_lite_chart")) == 3


def test_the_query_string_opens_a_hotel_and_a_day_and_the_held_flags_are_open(
    demo_file, monkeypatch
):
    testing = pytest.importorskip("streamlit.testing.v1")
    page = _page(testing, monkeypatch, demo_file, "full-service", 30, end=True)
    assert page.subheader[0].value == "Downtown full-service hotel, Wed 3 Feb 2027 [day 30]"
    assert page.sidebar.slider[0].value == 30
    assert page.sidebar.checkbox[0].value and len(page.metric) == 20  # ?end=1 turns it on
    text = _text(page)
    assert "No plan was queued today." in text
    assert page.expander[0].label == "Held flags: 1" and page.expander[0].proto.expanded
    held = "\n".join(block.value for block in page.expander[0].markdown)
    assert (
        "Wed 10 Feb [37] to Fri 12 Feb [39], comp median down. The best alternative, raise 5% "
        "on Wed, Fri; lower halfway to the new median on Thu, is \\$10 less than holding."
    ) in held
    # A day with no night stayed, and a query string the file does not know.
    page = _page(testing, monkeypatch, demo_file, "airport", 0)
    assert page.main.caption[0].value == "Airport hotel: nights already stayed, none yet"
    assert len(page.metric) == 0 and not page.sidebar.checkbox[0].value
    page = _page(testing, monkeypatch, demo_file, "nowhere", 999)
    assert page.subheader[0].value == "Downtown convention hotel, Mon 4 Jan 2027 [day 0]"


def test_the_decision_panel_shows_the_stored_requests_earlier_change_last(demo_file, monkeypatch):
    """The lifestyle hotel's day-20 page: the plan for stay date 75 ends with the earlier change
    the stored request listed, under its label and as the request wrote it, with the dollar sign
    escaped; nothing else on the page carries the label."""
    testing = pytest.importorskip("streamlit.testing.v1")
    page = _page(testing, monkeypatch, demo_file, "lifestyle", 20)
    blocks = [block.value for block in page.markdown]
    label = (
        "**Since the last change:** day 18: raised 10% to \\$264 on Sat 75; since then 2 rooms "
        "booked against 1 expected"
    )
    assert blocks.count(label) == 1 and sum("Since the last change" in b for b in blocks) == 1
    at = blocks.index(label)
    assert blocks[at - 1].startswith("**Accepted:** ") and "Sat 20 Mar [75]" in blocks[at - 1]
    assert at + 1 == len(blocks) or not blocks[at + 1].startswith("**Since")


def test_a_reason_with_two_dollar_amounts_shows_both_as_written(demo_file, monkeypatch, tmp_path):
    # Streamlit's markdown reads a pair of dollar signs as a formula, a bracket pair followed by
    # a parenthesis as a link, two tildes as strikethrough and angle brackets as an autolink.
    # The page escapes every such mark, so the markdown holds "\$120" and the reader sees "$120".
    testing = pytest.importorskip("streamlit.testing.v1")
    file = tmp_path / "demo.duckdb"
    shutil.copy(demo_file, file)
    connection = stored.connect(file)
    try:
        connection.execute(
            "UPDATE queue SET reason = 'A $120 raise earns $1,000 more than holding. "
            "See [the plan](http://example.com), ~~hold~~ and <http://example.com>.' "
            "WHERE as_of_day = 20 AND hotel = 'airport' AND queued"
        )
    finally:
        connection.close()
    page = _page(testing, monkeypatch, file, "airport", 20)
    text = _text(page)
    assert ("\\$10,140 more than holding. A \\$120 raise earns \\$1,000 more than holding.") in text
    assert "$120 raise earns $1,000" not in text
    assert (
        "See \\[the plan\\](http://example.com), \\~\\~hold\\~\\~ and \\<http://example.com\\>."
    ) in text


def test_at_four_ticks_the_day_20_page_names_the_ticks_in_the_news_and_the_legend(
    monkeypatch, tmp_path_factory
):
    """The airport hotel's day-20 page on a four-tick file: the news line names the filing's tick
    and the decision's tick with the raise's stay dates and what they earned, and the planned
    rate's legend entry names the tick it was decided at."""
    testing = pytest.importorskip("streamlit.testing.v1")
    from hotel_market.demo_data import build

    file = tmp_path_factory.mktemp("ticks") / "demo4.duckdb"
    build(7, file, ticks=4)
    page = _page(testing, monkeypatch, file, hotel="airport", day=20)
    text = _text(page)
    assert "The airlines filed a schedule change at tick 3 of 4: arriving passengers are" in text
    assert (
        "The first flag rose at tick 3 of 4, and the first raise was accepted at tick 3 of 4"
        in text
    )
    assert "against the fixed-rate run." in text
    assert "Planned rate (tick 3 of 4)" in _rate_chart_spec(page)
    assert [caption.value for caption in page.sidebar.caption][0].startswith(
        "Seed 7 of the simulated market. The reasons are the template's, as the recorded run is "
        "at one tick a day"
    )
