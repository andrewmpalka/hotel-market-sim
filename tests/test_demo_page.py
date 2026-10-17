"""Module 27, demo_page.py: the read-only page. It imports nothing from the package and does no
arithmetic on a figure; every figure it shows is a row code wrote."""

import ast
import json
import re
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
AIRPORT_HEADLINE = (  # the plan's headline, its dollar sign escaped
    "**+\\$10,140 over holding · raise 5% on Tuesday and Friday; raise 10% on Monday, Wednesday, "
    "Thursday and Sunday · Tue 23 Feb to Fri 23 Apr**"
)
AIRPORT_WHY = (  # then the recorded run's reason, its dollar signs escaped
    "<small>Why</small> "
    + json.loads((ROOT / "tests" / "fixtures" / "live_seed7" / "day020_airport.json").read_text())[
        "decisions"
    ][0]["reason"].replace("$", "\\$")
)
SIDEBAR = (  # the seed's place among the results' runs
    "One simulated five months, run 7 of the 20 in the results. Every figure is computed by code. "
    "The reasons are the model's own words."
)
STAND_IN = "Reasons marked * are the stand-in's, not the model's."
STRIP = ["Today's news", "Nights flagged", "Recommendations", "Value at stake today"]
RED_BANDS = "The red bands are the stay dates flagged today."
# The program's words, which only the engineers' expander may show. "flagged" is the exception,
# in the strip's label and the charts' caption, so "flag" matches only as a word of its own.
PROGRAMS_WORDS = re.compile(
    r"\b(?:seeds?|ticks?|digests?|fixed-rate|templates?|stand-in|queue[sd]?|flags?|files?)\b",
    re.IGNORECASE,
)


def _tree() -> ast.Module:
    return ast.parse(PAGE.read_text())


def _page(testing, monkeypatch, file, hotel=None, day=None, end=False, tick=None):
    """The page run on the file, opened at the hotel, day and tick the query string names, with
    the end-of-run result turned on by the query string when asked."""
    monkeypatch.setenv("HOTEL_MARKET_DEMO_FILE", str(file))
    page = testing.AppTest.from_file(str(PAGE), default_timeout=60)
    if hotel is not None:
        page.query_params["hotel"] = hotel
    if day is not None:
        page.query_params["day"] = str(day)
    if end:
        page.query_params["end"] = "1"
    if tick is not None:
        page.query_params["tick"] = str(tick)
    page.run()
    assert not page.exception
    return page


def _text(page) -> str:
    return "\n".join(block.value for block in page.markdown)


def _rate_chart_spec(page) -> str:
    """The rate chart's Vega-Lite spec, the first chart on the page."""
    return page.get("vega_lite_chart")[0].proto.spec


def _shown(page, engineers: bool = False) -> list[str]:
    """Every text a reader sees outside the expander for engineers, or with engineers=True only
    the text inside it: titles, captions, markdown other than the style sheets, the tiles, the
    expanders' labels and contents, and the sidebar's widgets."""
    inside = [e for e in page.expander if e.label == "For engineers"]
    if engineers:
        return [block.value for e in inside for block in e.markdown]
    hidden = {id(block.proto) for e in inside for block in e.markdown}
    texts = [header.value for header in page.header] + [s.value for s in page.subheader]
    texts += [caption.value for caption in page.caption]
    texts += [
        block.value
        for block in page.markdown
        if not block.value.startswith("<style>") and id(block.proto) not in hidden
    ]
    texts += [f"{m.label} {m.value} {m.delta}" for m in page.metric]
    texts += [e.label for e in page.expander]
    texts += [w.label for w in page.selectbox] + [o for w in page.selectbox for o in w.options]
    texts += [w.label for w in page.slider] + [w.label for w in page.checkbox]
    return texts


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
    assert page.subheader[0].value == "Downtown convention hotel · Mon 4 Jan 2027"
    assert '"planned_rate"' not in _rate_chart_spec(page)  # no accepted plan, no legend entry
    page.sidebar.selectbox[0].select("Airport hotel")
    page.sidebar.slider[0].set_value(20)
    page.run()
    assert not page.exception
    assert page.subheader[0].value == "Airport hotel · Sun 24 Jan 2027"
    assert page.main.caption[0].value == "day 20"
    # The strip under the title: the file's four tiles for the day, as stored.
    assert [metric.label for metric in page.metric][:4] == STRIP
    assert [metric.value for metric in page.metric][1:4] == ["60", "1", "+$10,140"]
    text = _text(page)
    assert (
        "The airlines filed a schedule change: arriving passengers are up 12.8% to 23.0% for "
        "Tue 23 Feb to Wed 2 Jun."
    ) in text
    assert "**Stay dates ahead, Sun 24 Jan to Fri 23 Apr.**" in text
    assert "**Today's recommendations**" in text and "Today's queue" not in text
    assert AIRPORT_HEADLINE in text and AIRPORT_WHY in text
    assert "Nothing else needed a decision today." in text
    assert [expander.label for expander in page.expander] == ["For engineers"]
    assert "Since our last change" not in text  # the airport's request listed no earlier change
    # The recommended rate is a dashed line in its own colour, with a legend entry.
    spec = _rate_chart_spec(page)
    assert '"planned_rate"' in spec and "#1baf7a" in spec and "#2a78d6" in spec
    assert (
        "'Recommended rate'" in spec and "'Usual pace'" in page.get("vega_lite_chart")[1].proto.spec
    )
    # The scorecard: the nights already stayed for the hotel and for all four, each labelled;
    # five tiles each, and no chip on a change that rounds to nothing. The five months are off.
    stayed = ["Airport hotel: 20 nights stayed", "All four hotels: 20 nights stayed"]
    assert [caption.value for caption in page.main.caption] == ["day 20", RED_BANDS, *stayed]
    labels = ["Occupancy", "ADR", "RevPAR", "Room revenue", "Contribution"]
    assert [metric.label for metric in page.metric] == STRIP + labels * 2
    assert page.metric[5].value == "$140.00" and page.metric[5].delta == ""
    assert not page.sidebar.checkbox[0].value and len(page.get("vega_lite_chart")) == 2
    # The sidebar says which run of the results this is, and defines contribution.
    assert [caption.value for caption in page.sidebar.caption] == [
        SIDEBAR,
        "Contribution is room revenue minus the cost of servicing every room sold.",
    ]
    assert page.sidebar.checkbox[0].label == "Show the full five months"
    # The checkbox adds the complete result for both scopes and the contribution line.
    page.sidebar.checkbox[0].check()
    page.run()
    assert not page.exception
    complete = "All five months: 150 nights"
    assert [caption.value for caption in page.main.caption] == [
        "day 20",
        RED_BANDS,
        stayed[0],
        complete,
        stayed[1],
        complete,
        "Contribution difference by stay date, once every stay date is complete",
    ]
    assert [metric.label for metric in page.metric] == STRIP + labels * 4
    assert page.metric[13].value == "$1,879,045" and page.metric[13].delta == "+$6,125"
    assert page.metric[23].value == "$14,505,130" and page.metric[23].delta == "+$19,796"
    assert len(page.get("vega_lite_chart")) == 3


def test_the_query_string_opens_a_hotel_and_a_day_and_the_held_flags_are_open(
    demo_file, monkeypatch
):
    testing = pytest.importorskip("streamlit.testing.v1")
    page = _page(testing, monkeypatch, demo_file, "full-service", 30, end=True)
    assert page.subheader[0].value == "Downtown full-service hotel · Wed 3 Feb 2027"
    assert page.sidebar.slider[0].value == 30
    assert page.sidebar.checkbox[0].value and len(page.metric) == 4 + 20  # ?end=1 turns it on
    text = _text(page)
    assert "No recommendation today." in text
    # The flags held by code sit in an expander, closed until the reader opens it.
    assert page.expander[0].label.startswith("Also looked at today:")
    assert page.expander[0].label == "Also looked at today: 1 held"
    assert not page.expander[0].proto.expanded
    held = "\n".join(block.value for block in page.expander[0].markdown)
    assert (
        "Wed 10 Feb to Fri 12 Feb, comp median down. The best alternative, raise 5% "
        "on Wed, Fri; lower halfway to the new median on Thu, is \\$10 less than holding."
    ) in held
    # A day with no night stayed, and a query string the file does not know.
    page = _page(testing, monkeypatch, demo_file, "airport", 0)
    assert "Airport hotel: no nights stayed yet" in [caption.value for caption in page.main.caption]
    assert len(page.metric) == 4 and not page.sidebar.checkbox[0].value  # the strip alone
    assert [metric.value for metric in page.metric] == ["Nothing new", "0", "0", "$0"]
    page = _page(testing, monkeypatch, demo_file, "nowhere", 999)
    assert page.subheader[0].value == "Downtown convention hotel · Mon 4 Jan 2027"


def test_the_decision_panel_shows_the_stored_requests_earlier_change_last(demo_file, monkeypatch):
    """The lifestyle hotel's day-20 page: the plan for stay date 75 ends with the earlier change
    the stored request listed, under its label and with dates for the request's day numbers, the
    dollar sign escaped; nothing else on the page carries the label."""
    testing = pytest.importorskip("streamlit.testing.v1")
    page = _page(testing, monkeypatch, demo_file, "lifestyle", 20)
    blocks = [block.value for block in page.markdown]
    label = (
        "**Since our last change on these dates:** Fri 22 Jan: raised 10% to \\$264 on Sat 20 Mar; "
        "since then 2 rooms booked against 1 expected"
    )
    assert blocks.count(label) == 1 and sum("Since our last change" in b for b in blocks) == 1
    at = blocks.index(label)
    assert blocks[at - 2] == "**+\\$730 over holding · raise 10% on Saturday · Sat 20 Mar**"
    assert blocks[at - 1].startswith("<small>Why</small> Stay date 75 is")
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
    assert "<small>Why</small> A \\$120 raise earns \\$1,000 more than holding." in text
    assert "$120 raise earns $1,000" not in text
    assert (
        "See \\[the plan\\](http://example.com), \\~\\~hold\\~\\~ and \\<http://example.com\\>."
    ) in text


def test_at_four_ticks_the_day_20_page_names_the_times_of_day_in_the_news_and_the_legend(
    monkeypatch, tmp_path_factory
):
    """The airport hotel's day-20 page on a four-tick file: the news line names the filing's time
    of day and the decision's with the raise's stay dates and what they earned, and the
    recommended rate's legend entry names the time it was decided at. The stand-in answers this
    file's requests, so the sidebar says so and each reason carries its mark."""
    testing = pytest.importorskip("streamlit.testing.v1")
    from hotel_market.demo_data import build

    file = tmp_path_factory.mktemp("ticks") / "demo4.duckdb"
    build(7, file, ticks=4)
    page = _page(testing, monkeypatch, file, hotel="airport", day=20)
    text = _text(page)
    assert page.subheader[0].value == "Airport hotel · Sun 24 Jan 2027 · 17:00"
    assert "At 14:00 the airlines filed a schedule change: arriving passengers are" in text
    assert "The first flag rose at 14:00, and the first raise was accepted at 14:00" in text
    assert "against the fixed-rate run." in text
    assert "Recommended rate (from 14:00)" in _rate_chart_spec(page)
    # The recording at this clock is the intraday market's, so the template answers, and the
    # sidebar marks its reasons.
    assert [caption.value for caption in page.sidebar.caption] == [
        SIDEBAR,
        STAND_IN,
        "Contribution is room revenue minus the cost of servicing every room sold.",
    ]
    page = _page(testing, monkeypatch, file, hotel="airport", day=20, tick=3)
    reasons = [block.value for block in page.markdown if block.value.startswith("<small>Why")]
    assert reasons and all(reason.endswith(" *") for reason in reasons)


def test_the_tick_slider_shows_the_state_as_of_a_tick(demo_file_intraday, demo_file, monkeypatch):
    """On a file written at four ticks a day the sidebar adds a time-of-day slider under the day
    slider, the day's last time by default, and the page shows the state as of the tick: on day
    25 at the lifestyle hotel, 08:00 has nothing yet and no recommendation, 11:00 has the
    concert's news, the accepted raise and the rate recommended from 11:00, and 17:00 adds the
    outcome line. The query string still names the tick by number. The daily file has no
    time-of-day slider and no time in its title."""
    testing = pytest.importorskip("streamlit.testing.v1")
    page = _page(testing, monkeypatch, demo_file_intraday, "lifestyle", 25, tick=1)
    assert page.subheader[0].value == "Lifestyle hotel · Fri 29 Jan 2027 · 08:00"
    assert [slider.label for slider in page.sidebar.slider] == ["Day"]
    assert [slider.label for slider in page.sidebar.select_slider] == ["Time of day"]
    assert page.sidebar.select_slider[0].value == "08:00"
    text = _text(page)
    assert "Nothing new has become known yet today." in text
    assert "No recommendation today." in text and '"planned_rate"' not in _rate_chart_spec(page)
    page.sidebar.select_slider[0].set_value("11:00")
    page.run()
    assert not page.exception
    assert page.subheader[0].value.endswith(" · 11:00")
    text = _text(page)
    assert "At 11:00 an event, the concert, was announced" in text
    assert (
        "**+\\$2,470 over holding · raise 10% on Thursday and Friday · Thu 4 Feb to Fri 5 Feb**"
        in text
    )
    assert "The first flag rose" not in text
    assert "Recommended rate (from 11:00)" in _rate_chart_spec(page)
    page = _page(testing, monkeypatch, demo_file_intraday, "lifestyle", 25)
    assert page.sidebar.select_slider[0].value == "17:00"  # the day's last tick by default
    assert page.subheader[0].value.endswith(" · 17:00")
    assert "The first flag rose at 11:00, and the first raise was accepted" in _text(page)
    page = _page(testing, monkeypatch, demo_file, "lifestyle", 20)
    assert [slider.label for slider in page.sidebar.slider] == ["Day"]
    assert not page.sidebar.select_slider
    assert page.subheader[0].value == "Lifestyle hotel · Sun 24 Jan 2027"


def test_the_engineers_expander_is_the_only_place_the_programs_words_appear(demo_file, monkeypatch):
    """The day-20 pages of the daily file speak to a revenue executive: outside the closed
    expander for engineers no text names the seed, a tick, a digest, the fixed-rate run, the
    template or the stand-in, the queue, a flag or the file. "flagged", in the strip's label and
    the charts' caption, is the one exception, and the stand-in's caption shows only on a file
    the stand-in answered. The expander names them."""
    testing = pytest.importorskip("streamlit.testing.v1")
    for hotel in ("airport", "lifestyle"):
        page = _page(testing, monkeypatch, demo_file, hotel, 20)
        shown = _shown(page)
        found = [word for text in shown for word in PROGRAMS_WORDS.findall(text)]
        assert not found, found
        assert any(text.startswith("Nights flagged") for text in shown) and RED_BANDS in shown
        engineers = [e for e in page.expander if e.label == "For engineers"]
        assert len(engineers) == 1 and not engineers[0].proto.expanded
        inside = _shown(page, engineers=True)
        assert inside[:2] == ["Seed 7. Day 20.", "Market file: demo"]
        assert inside[-1] == "This page reads a file demo\\_data.py wrote and computes nothing."
        digests = [line for line in inside if line.startswith("Request digest: ")]
        assert len(digests) == len([b for b in page.markdown if b.value.startswith("<small>Why")])
