"""demo_page.py

The read-only demo page: a Streamlit app over the file hotel-market demo-data writes.

    HOTEL_MARKET_DEMO_FILE=demo.duckdb streamlit run src/hotel_market/demo_page.py

The page reads the file and computes nothing. Every figure it shows is a row code wrote
(demo_data.py, sql/demo.sql), and the page only formats and draws it. A test fails if this module
imports anything from the package or does arithmetic on a figure. The sidebar picks one hotel and
one day, and the query string can name them (?hotel=convention&day=10). The sidebar also says
which of the results' runs this is, marks the stand-in's reasons when the file holds any, and
defines contribution. Under the title and the day's number come what became known that day and
three tiles: the nights flagged, the recommendations and their value at stake together. Two
charts follow, side by side, over the next two weeks with the nights flagged so far that day
shaded, or over the first flagged night to the last, two weeks at least, when one lies further
out: our rate, the comp set median and each recommended change as an arrow, and the rooms on
the books as bars against the usual pace. Their heading names the flagged nights, and when the
news names nights past the agent's window it adds how far the agent looks, from the file. Then
come the day's recommendations and the
scorecard: the nights already stayed for the hotel and for all the hotels together. Each
recommendation is one line led by its value at stake. Where the stored request listed the
hotel's earlier changes on a plan's stay dates, the next line shows them under "Since our last
change on these dates", with dates for the request's day numbers. The model's reason sits in a
closed expander under the plan, after a line that dates the request's numbers for its stay
dates, so the day reads first and the reason is one click away. The flags held by code sit in a
closed expander. A sidebar checkbox, off by default, adds the full five months:
the tiles once every stay date is complete and the contribution difference by stay date. The
query string can turn it on (&end=1). When the file was written on a finer clock, a time-of-day
slider under the day slider picks a tick of the day (&tick=2), the day's last by default, and the
page shows the state as of that tick: the news landed so far, every recommendation made so far
that day, each led by the time it was decided at and, once a later tick has come, the time it is
in effect from, the tiles counting them as "so far today", the flags held at that tick, and the
charts and the recommended rate as of it. The seed, the tick, the market's file and the
requests' digests sit in a closed expander for engineers at the bottom. Everything fits a 1440 by
900 window in both states and at every tick, which scripts/demo_screenshots.py checks; the
recommendations' text is set a size smaller than the page's and the news's lines tighter, so a
day with three accepted plans and two lines of news still fits. Streamlit is an optional extra:
pip install -e ".[demo]".
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
TICK_PARAMETER = "tick"  # the query parameter that names the tick of the day, on a finer clock
END_PARAMETER = "end"  # the query parameter that turns the end-of-run result on
NOTHING_YET = "Nothing new has become known yet today."  # a tick before the day's news lands
ON_VALUES = ("1", "true", "on", "yes")  # what the end parameter reads as on
ALL = "all"  # the scorecard's key for the hotels together, as demo_data writes it
PLOT_HEIGHTS = {
    "chart": 110,
    "small": 50,
}  # the plot areas, in pixels: a stay-date chart, the small line
AXIS_LABEL_SIZE = 12  # the axes' tick labels, in points
_NEXT_NIGHTS = 14  # the fewest nights the charts show: the next two weeks on a quiet day
_LABELLED_NIGHTS = 7  # up to this many flagged nights, the charts print each one's values
_BAND_GAP = 0.25  # the gap between two nights' bands on the axis, as a share of a night's slot
_SLOT = 1.3333333333333333  # a night's whole slot in bands, 1 / (1 - _BAND_GAP)
TILE_SIZES = {
    "compact": (0.75, 1.1),
    "large": (0.9, 1.2),
}  # a tile's label and value font sizes in rem: with the end-of-run result shown, and without
COLORS = {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a", "red": "#e34948"}  # the lines

# The Deploy button and the menu go, the header shrinks, and the tiles and gaps tighten so the
# whole page fits 900 pixels of height at 1440 wide.
STYLE = """<style>
[data-testid="stToolbar"] {display: none;}
[data-testid="stHeader"] {height: 2rem !important; background: transparent !important;}
.block-container {padding-top: 0.75rem; padding-bottom: 0.25rem;}
[data-testid="stVerticalBlock"] {gap: 0.2rem;}
h3 {padding-top: 0 !important; padding-bottom: 0.25rem !important; line-height: 1.05 !important;}
[data-testid="stMarkdownContainer"] p:has(> strong:only-child) {line-height: 1.25;}
[data-testid="stMetric"] {padding: 0;}
[data-testid="stMetricLabel"] {line-height: 1.1; min-height: 0;}
[data-testid="stMetric"] div:has(> [data-testid="stMetricDelta"]) {padding-bottom: 0;}
[data-testid="stMetricValue"] {line-height: 1.15; padding-bottom: 0;}
[data-testid="stMetricValue"] div {line-height: 1.15;}
[data-testid="stMetricDelta"] {padding-bottom: 0;}
[data-testid="stMetricDelta"] svg {width: 0.9rem; height: 0.9rem;}
[data-testid="stCaptionContainer"] {margin-bottom: 0 !important;}
[data-testid="stCaptionContainer"] p {font-size: 1rem; margin-bottom: 0; line-height: 1.15;}
[data-testid="stExpander"] details summary {padding: 0.1rem 0.5rem;}
.st-key-queue p {font-size: 0.9rem; line-height: 1.25;}
.st-key-news p {line-height: 1.2;}
.st-key-index {margin-top: 0.4rem;}
.st-key-index p {font-size: 0.8rem; line-height: 1.1;}
.st-key-strip [data-testid="stMetricLabel"] p {font-size: 0.8rem;}
.st-key-strip [data-testid="stMetricValue"] {font-size: 1rem;}
</style>"""

MARKDOWN_MARKS = ("\\", "$", "*", "_", "`")  # what the page escapes so a text shows as written
# What a reason has escaped: those marks and the link, image, strikethrough and autolink marks,
# which a model's text could hold.
REASON_MARKS = ("\\", "$", "*", "_", "`", "[", "]", "!", "~", "<", ">")


def _reader(connection):
    """A function giving a query's rows as a data frame."""

    def rows(sql: str, *parameters):
        return connection.execute(sql, list(parameters)).df()

    return rows


def plain(text: str, marks: tuple[str, ...] = MARKDOWN_MARKS) -> str:
    """The text with its markdown marks escaped, so a dollar sign is a dollar sign."""
    for mark in marks:
        text = text.replace(mark, f"\\{mark}")
    return text


def _tile_style(size: str) -> str:
    """The tiles' font sizes: compact with the end-of-run result shown, large without. The
    scorecard's captions follow the tiles, so a long hotel name keeps to one line when the
    column holds four rows of tiles."""
    label, value = TILE_SIZES[size]
    caption = "" if size == "large" else '[data-testid="stCaptionContainer"] p {font-size: 0.9rem;}'
    return (
        "<style>"
        f'[data-testid="stMetricLabel"] p {{font-size: {label}rem;}}'
        f'[data-testid="stMetricValue"] {{font-size: {value}rem;}}'
        f'[data-testid="stMetricDelta"] {{font-size: {label}rem;}}'
        f"{caption}"
        "</style>"
    )


def _axis(order: list[str], ticks: list[str]) -> alt.X:
    """The stay-date axis: every date in the window in order, the Mondays labelled, and the
    labels that would overlap left out."""
    return alt.X(
        "label:O",
        sort=order,
        title=None,
        axis=alt.Axis(
            values=ticks,
            labelAngle=0,
            labelFontSize=AXIS_LABEL_SIZE,
            labelOverlap=True,
            labelSeparation=8,
        ),
        scale=alt.Scale(paddingInner=_BAND_GAP, paddingOuter=0.15),
    )


def _y(field: str, title: str | None, **axis) -> alt.Y:
    """A value axis with the page's label size."""
    return alt.Y(field, title=title, axis=alt.Axis(labelFontSize=AXIS_LABEL_SIZE, **axis))


def _legend(
    label_expr: str | None = None, orient: str = "top", symbol: str = "stroke"
) -> alt.Legend:
    """A legend above the plot, off the lines, with stroke symbols that show a dash. Its labels are
    the axes' size, so "Recommended rate (from 11:00)" fits beside the other two."""
    legend = alt.Legend(
        orient=orient,
        title=None,
        symbolType=symbol,
        symbolStrokeWidth=2,
        offset=6,
        labelLimit=240,
        labelFontSize=AXIS_LABEL_SIZE,
    )
    if label_expr is not None:
        legend["labelExpr"] = label_expr
    return legend


def _series(lines: dict) -> dict:
    """The color and dash encodings of one chart's lines, sharing one legend. lines maps each
    line's field to its legend name, its color's name and its dash."""
    label = " : ".join(f"datum.label == '{key}' ? '{name}'" for key, (name, _, _) in lines.items())
    domain = list(lines)
    return {
        "color": alt.Color(
            "line:N",
            scale=alt.Scale(domain=domain, range=[COLORS[color] for _, color, _ in lines.values()]),
            legend=_legend(f"{label} : datum.label"),
        ),
        "strokeDash": alt.StrokeDash(
            "line:N",
            scale=alt.Scale(domain=domain, range=[dash for _, _, dash in lines.values()]),
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
    days = rows("SELECT as_of_day, label, stay_window, index FROM days ORDER BY as_of_day")
    run = rows("SELECT seed, ticks, market FROM run").iloc[0]
    ticks = int(run["ticks"])
    # shortcut: the slider names the four times of a four-tick day, so a file written at more
    # ticks offers only its first four; to offer more, write each tick's time into the file.
    times = dict(enumerate(["08:00", "11:00", "14:00", "17:00"][:ticks], 1))  # tick -> its time
    ticks_at = {time: tick for tick, time in times.items()}
    stand_in = not rows("SELECT 1 FROM queue WHERE reason_source = 'template' LIMIT 1").empty
    keys = hotels["key"].tolist()
    numbers = days["as_of_day"].tolist()
    wanted_hotel = st.query_params.get(HOTEL_PARAMETER)
    wanted_day = st.query_params.get(DAY_PARAMETER)
    wanted_tick = str(st.query_params.get(TICK_PARAMETER))
    wanted_end = str(st.query_params.get(END_PARAMETER)).lower()
    first_hotel = keys.index(wanted_hotel) if wanted_hotel in keys else 0
    first_day = numbers[0]
    if wanted_day is not None and wanted_day.isdigit() and int(wanted_day) in numbers:
        first_day = int(wanted_day)
    first_tick = ticks  # the day's last tick, the whole day, unless the query names one
    if wanted_tick.isdigit() and 1 <= int(wanted_tick) <= ticks:
        first_tick = int(wanted_tick)
    with st.sidebar:
        st.header("Hotel market demo")
        name = st.selectbox("Hotel", hotels["name"].tolist(), index=first_hotel)
        day = st.slider("Day", min_value=numbers[0], max_value=numbers[-1], value=first_day)
        time = (
            st.select_slider(
                "Time of day",
                options=list(times.values()),
                value=times.get(first_tick, list(times.values())[-1]),
            )
            if ticks > 1
            else ""
        )
        tick = ticks_at[time] if ticks > 1 else 1
        show_end = st.checkbox("Show the full five months", value=wanted_end in ON_VALUES)
        st.caption(
            f"One simulated five months, run {run['seed']} of the 20 in the results. Every figure "
            "is computed by code. The reasons are the model's own words."
        )
        if stand_in:
            st.caption("Reasons marked * are the stand-in's, not the model's.")
        st.caption("Contribution is room revenue minus the cost of servicing every room sold.")
    st.markdown(_tile_style("compact" if show_end else "large"), unsafe_allow_html=True)
    hotel = hotels.loc[hotels["name"] == name].iloc[0]
    key = hotel["key"]
    today = days.loc[days["as_of_day"] == day].iloc[0]

    # ---- the title and the strip, then what became known today ---------------------------------
    clock = f" · {time}" if ticks > 1 else ""
    st.subheader(f"{name} · {today['label']}{clock}")
    with st.container(key="index"):  # the key names the day's number for STYLE's small text
        st.caption(today["index"])
    news = rows(
        "SELECT text FROM news WHERE as_of_day = ? AND hotel = ? AND as_of_tick <= ? "
        "ORDER BY as_of_tick, position",
        day,
        key,
        tick,
    )
    with st.container(key="news"):  # the key names the news for STYLE's tighter lines
        st.markdown("  \n".join(plain(text) for text in news["text"].tolist()) or NOTHING_YET)
    strip = rows(
        "SELECT nights_flagged, recommendations, value_at_stake, horizon_text FROM strip "
        "WHERE as_of_day = ? AND hotel = ? AND as_of_tick = ?",
        day,
        key,
        tick,
    ).iloc[0]
    so_far = "so far today" if ticks > 1 else "today"  # a finer clock counts the day up to the tick
    with st.container(key="strip"):  # the key names the strip for STYLE
        tiles = st.columns(3)
        tiles[0].metric("Nights flagged", strip["nights_flagged"])
        tiles[1].metric(
            "Recommendations so far today" if ticks > 1 else "Recommendations",
            strip["recommendations"],
        )
        tiles[2].metric(f"Value at stake {so_far}", strip["value_at_stake"])

    # ---- the nights today's news touched --------------------------------------------------------
    stays = rows(
        "SELECT stay_day, label, tick, rate, comp_median, rooms_on_books, pace, flagged, "
        "causes, flag, planned_rate, decided_at FROM stay_dates WHERE as_of_day = ? AND hotel = ? "
        "AND as_of_tick = ? ORDER BY stay_day",
        day,
        key,
        tick,
    )
    flagged = stays.loc[stays["flagged"]]
    # The charts show the next two weeks, the nights flagged so far today shaded. When a flagged
    # night lies further out, they show the first flagged night to the last, two weeks at least,
    # so the nights between keep their places on the axis.
    shown = stays.head(_NEXT_NIGHTS)
    if not flagged.empty and flagged.index[-1] not in shown.index:
        shown = stays.loc[flagged.index[0] : flagged.index[-1]]
        if len(shown) < _NEXT_NIGHTS:
            shown = stays.loc[: flagged.index[-1]].tail(_NEXT_NIGHTS)  # the two weeks to the last
    labels = shown["label"].tolist()
    # The flagged nights as runs of consecutive nights: "Thu 18 Feb, Sat 20 Feb to Sun 21 Feb".
    starts = shown["flagged"] & ~shown["flagged"].shift(fill_value=False)
    ends = shown["flagged"] & ~shown["flagged"].shift(-1, fill_value=False)
    runs = [
        first if first == last else f"{first} to {last}"
        for first, last in zip(shown.loc[starts, "label"], shown.loc[ends, "label"])
    ]
    shade = not (flagged.empty or shown["flagged"].all())  # set the flagged nights apart
    few = 0 < len(flagged) <= _LABELLED_NIGHTS  # few enough flagged nights to print each value
    axis = _axis(labels, labels)
    planned = shown.loc[shown["planned_rate"].notna()]
    moved = planned.loc[planned["planned_rate"] != planned["rate"]]  # the nights a plan changes
    stay_date = alt.Tooltip("label:N", title="Stay date")
    money = {"format": "$,.0f"}
    # Our rate and the market's median as lines, our rate as a dot with its value on a few flagged
    # nights, and each recommended change as an arrow from our rate to the new one. The axis fits
    # the nights, with room above and below, so a 5% move shows, and its labels stay whole
    # dollars apart, so no two read the same.
    names = {"rate": "Our rate", "comp_median": "Comp set median"}
    if not moved.empty:  # once the rate has moved, our rate shows it and the arrow goes
        decided_at = moved.iloc[0]["decided_at"]  # "14:00" on a finer clock, else empty
        names["planned_rate"] = (
            f"Recommended rate (from {decided_at})" if decided_at else "Recommended rate"
        )
    colors = {"rate": "blue", "comp_median": "orange", "planned_rate": "aqua"}
    series = alt.Color(
        "series:N",
        scale=alt.Scale(domain=list(names.values()), range=[COLORS[colors[key]] for key in names]),
        legend=_legend(symbol="circle"),
    )
    dollars = alt.Y(
        "rate:Q",
        title="Rate ($)",
        scale=alt.Scale(zero=False, nice=True, padding=20),
        axis=alt.Axis(labelFontSize=AXIS_LABEL_SIZE, tickCount=8, tickMinStep=1, **money),
    )
    ours = alt.Chart(shown.assign(series=names["rate"]))
    market = alt.Chart(shown.assign(series=names["comp_median"]))
    our_tip = [stay_date, alt.Tooltip("rate:Q", title="Our rate", **money)]
    market_tip = [stay_date, alt.Tooltip("comp_median:Q", title="Comp set median", **money)]
    layers = [
        market.mark_line(strokeWidth=1.5, opacity=0.8).encode(
            x=axis, y=alt.Y("comp_median:Q"), color=series, tooltip=market_tip
        ),
        ours.mark_line(strokeWidth=2.5).encode(x=axis, y=dollars, color=series, tooltip=our_tip),
    ]
    if few:
        marked = alt.Chart(flagged.assign(series=names["rate"]))
        layers.extend(
            [
                marked.mark_point(filled=True, size=80, opacity=1).encode(
                    x=axis, y=alt.Y("rate:Q"), color=series, tooltip=our_tip
                ),
                marked.mark_text(dy=16, fontSize=AXIS_LABEL_SIZE, color="white").encode(
                    x=axis, y=alt.Y("rate:Q"), text=alt.Text("rate:Q", **money)
                ),
            ]
        )
    if not moved.empty:
        layers.append(
            alt.Chart(moved.assign(series=names["planned_rate"]))
            .mark_rule(strokeWidth=3)
            .encode(x=axis, y="rate:Q", y2="planned_rate:Q", color=series)
        )
    # Each arrowhead points the way the rate moves, a raise's up and a cut's down, with the new
    # rate printed beyond it.
    cut = moved["planned_rate"] < moved["rate"]
    arrows = ((moved.loc[~cut], "triangle-up", -14), (moved.loc[cut], "triangle-down", 14))
    for part, shape, dy in arrows:
        if part.empty:
            continue
        chosen = alt.Chart(part.assign(series=names["planned_rate"]))
        layers.append(
            chosen.mark_point(filled=True, size=90, shape=shape, opacity=1).encode(
                x=axis,
                y=alt.Y("planned_rate:Q"),
                color=series,
                tooltip=[
                    stay_date,
                    alt.Tooltip("rate:Q", title="Our rate", **money),
                    alt.Tooltip("planned_rate:Q", title="Recommended", **money),
                ],
            )
        )
        if few:
            layers.append(
                chosen.mark_text(dy=dy, fontSize=AXIS_LABEL_SIZE, color="white").encode(
                    x=axis, y=alt.Y("planned_rate:Q"), text=alt.Text("planned_rate:Q", **money)
                )
            )
    # The rooms on the books as bars, printed over a few flagged nights, and the usual pace by now
    # as a line.
    kinds = {"rooms_on_books": "Rooms on the books", "pace": "Usual pace"}
    paced = alt.Color(
        "series:N",
        scale=alt.Scale(domain=list(kinds.values()), range=[COLORS["aqua"], COLORS["orange"]]),
        legend=_legend(symbol="square"),
    )
    rooms_y = alt.Y(
        "rooms_on_books:Q",
        title="Rooms",
        scale=alt.Scale(domainMin=0, nice=True),
        axis=alt.Axis(labelFontSize=AXIS_LABEL_SIZE, tickCount=5),
    )
    booked = alt.Chart(shown.assign(series=kinds["rooms_on_books"]))
    pace = alt.Chart(shown.assign(series=kinds["pace"]))
    pace_tip = [stay_date, alt.Tooltip("pace:Q", title="Usual pace", format=",.0f")]
    rooms = [
        booked.mark_bar(opacity=0.85).encode(
            x=axis,
            y=rooms_y,
            color=paced,
            tooltip=[stay_date, alt.Tooltip("rooms_on_books:Q", title="Rooms on the books")],
        ),
        pace.mark_line(strokeWidth=2).encode(
            x=axis, y=alt.Y("pace:Q"), color=paced, tooltip=pace_tip
        ),
    ]
    if few:
        rooms.append(
            alt.Chart(flagged)
            .mark_text(dy=-9, fontSize=AXIS_LABEL_SIZE, color="white")
            .encode(x=axis, y=alt.Y("rooms_on_books:Q"), text="rooms_on_books:Q")
        )
    # A grey band behind the flagged nights, under both charts' marks. Each night's band fills its
    # whole slot on the axis, so a run of flagged nights reads as one band. (Vega-Lite's x2 on
    # this axis would draw one rect per run, but it lands the run's end on the wrong night.)
    if shade:
        band = (
            alt.Chart(flagged)
            .mark_rect(color="#888888", opacity=0.22, width={"band": _SLOT}, align="center")
            .encode(x=axis)
        )
        layers.insert(0, band)
        rooms.insert(0, band)
    heading = f"Nothing flagged today. The next two weeks: {labels[0]} to {labels[-1]}"
    if runs:
        nights = runs[0] if len(runs) == 1 else f"{', '.join(runs[:-1])} and {runs[-1]}"
        heading = f"Flagged today{', shaded' if shade else ''}: {nights}"
    # When the news names nights past the agent's window, the heading says how far it looks.
    ahead = f" {strip['horizon_text']}" if strip["horizon_text"] else ""
    st.markdown(f"**{plain(heading)}.{plain(ahead)}**")
    left, right = st.columns(2)
    height = PLOT_HEIGHTS["chart"]
    left.altair_chart(_sized(alt.layer(*layers), height), width="stretch")
    right.altair_chart(_sized(alt.layer(*rooms), height), width="stretch")

    # ---- today's recommendations and the scorecard, side by side ------------------------------
    queue = rows(
        "SELECT as_of_tick, stays, causes, reason, reason_source, outcome, queued, alternative, "
        "alternative_text, since_last_change_text, headline, request_digest, stay_numbers_text, "
        "decided_at, in_effect FROM queue "
        "WHERE as_of_day = ? AND hotel = ? AND as_of_tick <= ? ORDER BY as_of_tick, position",
        day,
        key,
        tick,
    )
    plans = queue.loc[queue["queued"]]  # the day's plans so far, from every tick up to this one
    held = queue.loc[~queue["queued"] & (queue["as_of_tick"] == tick)]  # the flags held at it
    left, right = st.columns([5, 6])
    with left.container(key="queue"):  # the key names the panel for STYLE's smaller text
        st.markdown("**Today's recommendations**")
        if plans.empty:
            st.markdown(f"No recommendation {so_far}.")
        for plan in plans.itertuples():
            held_by_model = "Held: " if plan.outcome == "declined" else ""
            at = f"{plan.decided_at} · " if plan.decided_at else ""  # its time, on a finer clock
            effect = f" · {plan.in_effect}" if plan.in_effect and plan.as_of_tick < tick else ""
            star = " *" if plan.reason_source == "template" else ""
            st.markdown(f"**{held_by_model}{plain(f'{at}{plan.headline}{effect}')}**")
            if plan.since_last_change_text:  # the stored request's own line, with dates
                st.markdown(
                    f"**Since our last change on these dates:** "
                    f"{plain(plan.since_last_change_text)}"
                )
            with st.expander("Why", expanded=False):  # the model's words, one click away
                st.caption(plain(plan.stay_numbers_text))
                st.markdown(f"{plain(plan.reason, REASON_MARKS)}{star}")
        if held.empty:
            st.markdown("Nothing else needed a decision today.")
        else:
            with st.expander(f"Also looked at today: {len(held)} held", expanded=False):
                for flag in held.itertuples():
                    st.markdown(
                        plain(
                            f"{flag.stays}, {flag.causes}. The best alternative, "
                            f"{flag.alternative}, is {flag.alternative_text}."
                        )
                    )
    with right:
        st.markdown("**So far this run: with the agent / without it**")
        stayed = rows(
            "SELECT hotel, title, night_count, position, measure, value_text, delta_text "
            "FROM scorecard WHERE as_of_day = ? AND hotel IN (?, ?) ORDER BY position",
            day,
            key,
            ALL,
        )
        outcome = rows(
            "SELECT hotel, title, night_count, position, measure, value_text, delta_text "
            "FROM outcome WHERE hotel IN (?, ?) ORDER BY position",
            key,
            ALL,
        )
        for scope in (key, ALL):
            own = stayed.loc[stayed["hotel"] == scope]
            final = outcome.loc[outcome["hotel"] == scope]
            title = final.iloc[0]["title"]
            if own.empty:
                st.caption(f"{title}: no nights stayed yet")
            else:
                count = own.iloc[0]["night_count"]
                st.caption(f"{title}: {count} {'night' if count == 1 else 'nights'} stayed")
                _tiles(own)
            if show_end:
                st.caption(f"All five months: {final.iloc[0]['night_count']} nights")
                _tiles(final)
        if show_end:
            _gain_line(rows, key, stay_date)

    # ---- for engineers: the program's own words, closed by default -----------------------------
    at = f", tick {tick} of {ticks}" if ticks > 1 else ""
    with st.expander("For engineers", expanded=False):
        st.markdown(f"Seed {run['seed']}. Day {day}{at}.")
        st.markdown(plain(f"Market file: {run['market']}"))
        for plan in plans.itertuples():
            st.markdown(f"Request digest: {plan.request_digest}")
        st.markdown(plain("This page reads a file demo_data.py wrote and computes nothing."))


def _gain_line(rows, key: str, stay_date: alt.Tooltip) -> None:
    """The small line: the contribution difference by stay date once every stay date is
    complete, for the hotel and for all together."""
    gains = rows(
        "SELECT hotel, title, stay_day, label, tick, difference FROM gains "
        "WHERE hotel IN (?, ?) ORDER BY stay_day, hotel",
        key,
        ALL,
    )
    own = gains.loc[gains["hotel"] == key]
    together = gains.loc[gains["hotel"] == ALL]
    st.caption("Contribution difference by stay date, once every stay date is complete")
    line = (
        alt.Chart(gains)
        .mark_line(strokeWidth=1.5)
        .encode(
            x=_axis(own["label"].tolist(), own.loc[own["tick"], "label"].tolist()),
            y=_y("difference:Q", None, format="$,.0f"),
            color=alt.Color(
                "title:N",
                scale=alt.Scale(
                    domain=[own.iloc[0]["title"], together.iloc[0]["title"]],
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
    run. A change that reads as nothing, such as "0", draws no chip."""
    columns = st.columns(len(frame))
    for tile in frame.itertuples():
        nothing = tile.delta_text in ("0", "+0", "-0", "0.0%", "+0.0%", "-0.0%")
        columns[tile.position].metric(
            tile.measure, tile.value_text, None if nothing else tile.delta_text
        )


if __name__ == "__main__":
    main()
