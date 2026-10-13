"""demo_page.py

The read-only demo page: a Streamlit app over the file hotel-market demo-data writes.

    HOTEL_MARKET_DEMO_FILE=demo.duckdb streamlit run src/hotel_market/demo_page.py

The page reads the file and computes nothing. Every figure it shows is a row code wrote
(demo_data.py, sql/demo.sql), and the page only formats and draws it. A test fails if this module
imports anything from the package or does arithmetic on a figure. The sidebar picks one hotel and
one day, and the query string can name them (?hotel=convention&day=10). The page then shows what
became known that day, the stay dates ahead as two charts side by side, the day's queue with its
reasons and held flags, and the scorecard: the nights already stayed, the result once every stay
date is complete, and the contribution difference by stay date, for the hotel and for all the
hotels together. Everything fits a 1440 by 900 window, which scripts/demo_screenshots.py checks.
Streamlit is an optional extra: pip install -e ".[demo]".
"""

import os
from pathlib import Path

import altair as alt
import duckdb
import streamlit as st

FILE_VARIABLE = "HOTEL_MARKET_DEMO_FILE"  # the environment variable that names the file
DEFAULT_FILE = "demo.duckdb"  # the file when the variable is not set
HOTEL_PARAMETER = "hotel"  # the query parameter that names the hotel, by its key
DAY_PARAMETER = "day"  # the query parameter that names the day
ALL = "all"  # the scorecard's key for the hotels together, as demo_data writes it
PLOT_HEIGHTS = {
    "chart": 110,
    "small": 50,
}  # the plot areas, in pixels: a stay-date chart, the small line
COLORS = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "red": "#e34948"}  # the lines

# The Deploy button and the menu go, the header shrinks, and the tiles and gaps tighten so the
# whole page fits 900 pixels of height at 1440 wide.
STYLE = """<style>
[data-testid="stToolbar"] {display: none;}
[data-testid="stHeader"] {height: 2rem !important; background: transparent !important;}
.block-container {padding-top: 2.25rem; padding-bottom: 0.25rem;}
[data-testid="stVerticalBlock"] {gap: 0.3rem;}
h3 {padding-top: 0 !important; padding-bottom: 0.25rem !important;}
[data-testid="stMetric"] {padding: 0;}
[data-testid="stMetricLabel"] {line-height: 1.1;}
[data-testid="stMetricLabel"] p {font-size: 0.75rem;}
[data-testid="stMetricValue"] {font-size: 1.1rem; line-height: 1.15; padding-bottom: 0;}
[data-testid="stMetricValue"] div {line-height: 1.15;}
[data-testid="stMetricDelta"] {font-size: 0.75rem; padding-bottom: 0;}
[data-testid="stMetricDelta"] svg {width: 0.8rem; height: 0.8rem;}
[data-testid="stCaptionContainer"] {margin-bottom: 0 !important;}
[data-testid="stCaptionContainer"] p {margin-bottom: 0; line-height: 1.25;}
[data-testid="stExpander"] details summary {padding: 0.25rem 0.5rem;}
</style>"""

MARKDOWN_MARKS = ("\\", "$", "*", "_", "`")  # what the page escapes so a text shows as written


def _reader(connection):
    """A function giving a query's rows as a data frame."""

    def rows(sql: str, *parameters):
        return connection.execute(sql, list(parameters)).df()

    return rows


def plain(text: str) -> str:
    """The text with its markdown marks escaped, so a dollar sign is a dollar sign."""
    for mark in MARKDOWN_MARKS:
        text = text.replace(mark, f"\\{mark}")
    return text


def _axis(order: list[str], ticks: list[str]) -> alt.X:
    """The stay-date axis: every date in the window in order, the Mondays labelled, and the
    labels that would overlap left out."""
    return alt.X(
        "label:O",
        sort=order,
        title=None,
        axis=alt.Axis(
            values=ticks, labelAngle=0, labelFontSize=10, labelOverlap=True, labelSeparation=8
        ),
        scale=alt.Scale(paddingInner=0, paddingOuter=0),
    )


def _legend(label_expr: str | None = None, orient: str = "top") -> alt.Legend:
    """A legend above the plot, off the lines, with stroke symbols that show a dash."""
    legend = alt.Legend(
        orient=orient,
        title=None,
        symbolType="stroke",
        symbolStrokeWidth=2,
        offset=6,
        labelLimit=240,
    )
    if label_expr is not None:
        legend["labelExpr"] = label_expr
    return legend


def _series(domain: list[str], colors: list[str], dashes: list[list[int]], names: dict) -> dict:
    """The color and dash encodings of one chart's lines, sharing one legend."""
    label = " : ".join(f"datum.label == '{key}' ? '{name}'" for key, name in names.items())
    return {
        "color": alt.Color(
            "line:N",
            scale=alt.Scale(domain=domain, range=colors),
            legend=_legend(f"{label} : datum.label"),
        ),
        "strokeDash": alt.StrokeDash(
            "line:N",
            scale=alt.Scale(domain=domain, range=dashes),
            legend=_legend(f"{label} : datum.label"),
        ),
    }


def _sized(chart, height: int):
    """The chart as wide as its column and as tall as its plot, legend and axis need. Without
    this, Streamlit fits the whole chart into the plot height."""
    return chart.properties(
        height=height,
        width="container",
        padding={"top": 2, "bottom": 0, "left": 5, "right": 5},
        autosize=alt.AutoSizeParams(type="fit-x", contains="padding"),
    )


def main() -> None:
    """The page, run by streamlit as __main__; importing the module draws nothing."""
    st.set_page_config(page_title="Hotel market demo", layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)

    file = Path(os.environ.get(FILE_VARIABLE, DEFAULT_FILE))
    if not file.exists():
        st.error(f"{file} is not there. Run: hotel-market demo-data --seed 7 --out {file}")
        st.stop()
    connection = duckdb.connect(str(file), read_only=True)
    rows = _reader(connection)
    hotels = rows(
        "SELECT key, name, rooms, rate_axis_low, rate_axis_high FROM hotels ORDER BY position"
    )
    days = rows("SELECT as_of_day, label, stay_window FROM days ORDER BY as_of_day")
    keys = hotels["key"].tolist()
    numbers = days["as_of_day"].tolist()
    wanted_hotel = st.query_params.get(HOTEL_PARAMETER)
    wanted_day = st.query_params.get(DAY_PARAMETER)
    first_hotel = keys.index(wanted_hotel) if wanted_hotel in keys else 0
    first_day = numbers[0]
    if wanted_day is not None and wanted_day.isdigit() and int(wanted_day) in numbers:
        first_day = int(wanted_day)
    with st.sidebar:
        st.header("Hotel market demo")
        name = st.selectbox("Hotel", hotels["name"].tolist(), index=first_hotel)
        day = st.slider("Day", min_value=numbers[0], max_value=numbers[-1], value=first_day)
        st.caption(
            "Seed 7 of the simulated market. The reasons are the model's, from the recorded "
            "live run. The page reads a file code wrote and computes nothing."
        )
    hotel = hotels.loc[hotels["name"] == name].iloc[0]
    key = hotel["key"]
    today = days.loc[days["as_of_day"] == day].iloc[0]

    # ---- what became known today ----------------------------------------------------------------
    st.subheader(f"{name}, {today['label']}")
    news = rows(
        "SELECT text FROM news WHERE as_of_day = ? AND hotel = ? ORDER BY position", day, key
    )
    st.markdown("  \n".join(plain(text) for text in news["text"].tolist()))

    # ---- the stay dates ahead -------------------------------------------------------------------
    stays = rows(
        "SELECT stay_day, label, tick, rate, comp_median, rooms_on_books, pace, flagged, "
        "causes, flag, planned_rate FROM stay_dates WHERE as_of_day = ? AND hotel = ? "
        "ORDER BY stay_day",
        day,
        key,
    )
    axis = _axis(stays["label"].tolist(), stays.loc[stays["tick"], "label"].tolist())
    flagged = stays.loc[stays["flagged"]]
    planned = stays.loc[stays["planned_rate"].notna()].assign(line="planned_rate")
    marks = (
        alt.Chart(flagged)
        .mark_rect(color=COLORS["red"], opacity=0.2)
        .encode(x=axis, tooltip=[alt.Tooltip("label:N", title="Flagged"), "causes:N"])
    )
    rate_lines = _series(
        ["rate", "comp_median", "planned_rate"],
        [COLORS["blue"], COLORS["orange"], COLORS["blue"]],
        [[1, 0], [1, 0], [6, 4]],
        {"rate": "Our rate", "comp_median": "Comp set median", "planned_rate": "Planned rate"},
    )
    dollars = alt.Y(
        "dollars:Q",
        title="Rate ($)",
        scale=alt.Scale(domain=[float(hotel["rate_axis_low"]), float(hotel["rate_axis_high"])]),
    )
    stay_date = alt.Tooltip("label:N", title="Stay date")
    rates = (
        alt.Chart(stays)
        .transform_fold(["rate", "comp_median"], as_=["line", "dollars"])
        .mark_line(strokeWidth=2, clip=True)
        .encode(
            x=axis,
            y=dollars,
            tooltip=[stay_date, alt.Tooltip("dollars:Q", format="$,.0f")],
            **rate_lines,
        )
    )
    plan = (
        alt.Chart(planned)
        .mark_line(strokeWidth=2, clip=True)
        .encode(
            x=axis,
            y=alt.Y("planned_rate:Q", title="Rate ($)"),
            detail="flag:N",
            tooltip=[stay_date, alt.Tooltip("planned_rate:Q", title="Planned", format="$,.0f")],
            **rate_lines,
        )
    )
    room_lines = _series(
        ["rooms_on_books", "pace"],
        [COLORS["aqua"], COLORS["orange"]],
        [[1, 0], [1, 0]],
        {"rooms_on_books": "Rooms on the books", "pace": "Pace curve"},
    )
    rooms = (
        alt.Chart(stays)
        .transform_fold(["rooms_on_books", "pace"], as_=["line", "rooms"])
        .mark_line(strokeWidth=2)
        .encode(
            x=axis,
            y=alt.Y("rooms:Q", title="Rooms"),
            tooltip=[stay_date, alt.Tooltip("rooms:Q", format=",.0f")],
            **room_lines,
        )
    )
    st.markdown(
        f"**Stay dates ahead, {plain(today['stay_window'])}.** The red bands are the stay dates "
        "the agent flagged today."
    )
    left, right = st.columns(2)
    height = PLOT_HEIGHTS["chart"]
    left.altair_chart(_sized(alt.layer(marks, rates, plan), height), width="stretch")
    right.altair_chart(_sized(alt.layer(marks, rooms), height), width="stretch")

    # ---- today's queue and the scorecard, side by side ----------------------------------------
    queue = rows(
        "SELECT stays, causes, plan, value_text, reason, outcome, queued, alternative, "
        "alternative_text FROM queue WHERE as_of_day = ? AND hotel = ? ORDER BY position",
        day,
        key,
    )
    plans = queue.loc[queue["queued"]]
    held = queue.loc[~queue["queued"]]
    left, right = st.columns([4, 7])
    with left:
        st.markdown("**Today's queue**")
        if plans.empty:
            st.markdown("No plan was queued today.")
        for plan in plans.itertuples():
            words = plain(f"{plan.plan} for {plan.stays}, {plan.value_text}. {plan.reason}")
            st.markdown(f"**{plan.outcome.capitalize()}:** {words}")
        if held.empty:
            st.markdown("No flag was held today.")
        else:
            with st.expander(f"Held flags: {len(held)}", expanded=True):
                for flag in held.itertuples():
                    st.markdown(
                        plain(
                            f"{flag.stays}, {flag.causes}. The best alternative, "
                            f"{flag.alternative}, is {flag.alternative_text}."
                        )
                    )
    with right:
        st.markdown("**Scorecard, the agent run against the fixed-rate run**")
        stayed = rows(
            "SELECT hotel, title, nights, position, measure, value_text, delta_text "
            "FROM scorecard WHERE as_of_day = ? AND hotel IN (?, ?) ORDER BY position",
            day,
            key,
            ALL,
        )
        outcome = rows(
            "SELECT hotel, title, nights, position, measure, value_text, delta_text "
            "FROM outcome WHERE hotel IN (?, ?) ORDER BY position",
            key,
            ALL,
        )
        for scope in (key, ALL):
            own = stayed.loc[stayed["hotel"] == scope]
            final = outcome.loc[outcome["hotel"] == scope]
            title = final.iloc[0]["title"]
            if own.empty:
                st.caption(f"{title}: nights already stayed, none yet")
            else:
                st.caption(f"{title}: nights already stayed, {own.iloc[0]['nights']}")
                _tiles(own)
            st.caption(f"{title}: once every stay date is complete, {final.iloc[0]['nights']}")
            _tiles(final)
        gains = rows(
            "SELECT hotel, title, stay_day, label, tick, difference FROM gains "
            "WHERE hotel IN (?, ?) ORDER BY stay_day, hotel",
            key,
            ALL,
        )
        own_gains = gains.loc[gains["hotel"] == key]
        together = gains.loc[gains["hotel"] == ALL]
        st.caption("Contribution difference by stay date, once every stay date is complete")
        line = (
            alt.Chart(gains)
            .mark_line(strokeWidth=1.5)
            .encode(
                x=_axis(
                    own_gains["label"].tolist(), own_gains.loc[own_gains["tick"], "label"].tolist()
                ),
                y=alt.Y("difference:Q", title=None, axis=alt.Axis(format="$,.0f")),
                color=alt.Color(
                    "title:N",
                    scale=alt.Scale(
                        domain=[own_gains.iloc[0]["title"], together.iloc[0]["title"]],
                        range=[COLORS["blue"], COLORS["aqua"]],
                    ),
                    legend=_legend(orient="right"),
                ),
                tooltip=[
                    alt.Tooltip("title:N", title="Scope"),
                    stay_date,
                    alt.Tooltip("difference:Q", title="Difference", format="$,.0f"),
                ],
            )
        )
        st.altair_chart(_sized(line, PLOT_HEIGHTS["small"]), width="stretch")


def _tiles(frame) -> None:
    """One row of metric tiles, one per measure, each with the change against the fixed-rate
    run. A change written "0" shows with no arrow."""
    columns = st.columns(len(frame))
    for tile in frame.itertuples():
        columns[tile.position].metric(tile.measure, tile.value_text, tile.delta_text)


if __name__ == "__main__":
    main()
