"""demo_page.py

The read-only demo page: a Streamlit app over the file hotel-market demo-data writes.

    HOTEL_MARKET_DEMO_FILE=demo.duckdb streamlit run src/hotel_market/demo_page.py

The page reads the file and computes nothing. Every figure it shows is a row code wrote
(demo_data.py, sql/demo.sql), and the page only formats and draws it. A test fails if this module
imports anything from the package or does arithmetic on a figure. The sidebar picks one hotel and
one day. The page then shows what became known that day, the stay dates ahead as a chart, the
day's queue with its reasons, and the scorecard to date against the fixed-rate run. Streamlit is
an optional extra: pip install -e ".[demo]".
"""

import os
from pathlib import Path

import altair as alt
import duckdb
import streamlit as st

FILE_VARIABLE = "HOTEL_MARKET_DEMO_FILE"  # the environment variable that names the file
DEFAULT_FILE = "demo.duckdb"  # the file when the variable is not set


def _reader(connection):
    """A function giving a query's rows as a data frame."""

    def rows(sql: str, *parameters):
        return connection.execute(sql, list(parameters)).df()

    return rows


def main() -> None:
    """The page, run by streamlit as __main__; importing the module draws nothing."""
    st.set_page_config(page_title="Hotel market demo", layout="wide")
    st.markdown(
        "<style>.block-container {padding-top: 1.2rem; padding-bottom: 0.5rem}</style>",
        unsafe_allow_html=True,
    )

    file = Path(os.environ.get(FILE_VARIABLE, DEFAULT_FILE))
    if not file.exists():
        st.error(f"{file} is not there. Run: hotel-market demo-data --seed 7 --out {file}")
        st.stop()
    connection = duckdb.connect(str(file), read_only=True)
    rows = _reader(connection)
    hotels = rows("SELECT key, name, rooms FROM hotels ORDER BY position")
    days = rows("SELECT DISTINCT as_of_day FROM scorecard ORDER BY as_of_day")["as_of_day"].tolist()
    with st.sidebar:
        st.header("Hotel market demo")
        name = st.selectbox("Hotel", hotels["name"].tolist())
        day = st.slider("Day", min_value=days[0], max_value=days[-1], value=days[0])
        st.caption(
            "Seed 7 of the simulated market. The reasons are the model's, from the recorded "
            "live run. The page reads a file code wrote and computes nothing."
        )
    hotel = hotels.loc[hotels["name"] == name].iloc[0]
    key = hotel["key"]

    # ---- what became known today ----------------------------------------------------------------
    st.subheader(f"{name}, day {day}")
    news = rows(
        "SELECT text FROM news WHERE as_of_day = ? AND hotel = ? ORDER BY position", day, key
    )
    st.markdown("  \n".join(news["text"].tolist()))

    # ---- the stay dates ahead -------------------------------------------------------------------
    stays = rows(
        "SELECT stay_day, rate, comp_median, rooms_on_books, pace, flagged, causes "
        "FROM stay_dates WHERE as_of_day = ? AND hotel = ? ORDER BY stay_day",
        day,
        key,
    )
    flagged = stays.loc[stays["flagged"]]
    marks = (
        alt.Chart(flagged)
        .mark_rule(color="#d62728", opacity=0.25, size=6)
        .encode(x="stay_day:Q", tooltip=["stay_day:Q", "causes:N"])
    )
    rates = (
        alt.Chart(stays)
        .transform_fold(["rate", "comp_median"], as_=["line", "dollars"])
        .mark_line()
        .encode(
            x=alt.X("stay_day:Q", title="Stay date"),
            y=alt.Y("dollars:Q", title="Rate ($)", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "line:N",
                title=None,
                scale=alt.Scale(domain=["rate", "comp_median"], range=["#1f77b4", "#7f7f7f"]),
                legend=alt.Legend(
                    orient="top-right",
                    labelExpr="datum.label == 'rate' ? 'Our rate' : 'Comp set median'",
                ),
            ),
        )
        .properties(height=170, title="Our rate and the comp set median")
    )
    pace = (
        alt.Chart(stays)
        .transform_fold(["rooms_on_books", "pace"], as_=["line", "rooms"])
        .mark_line()
        .encode(
            x=alt.X("stay_day:Q", title="Stay date"),
            y=alt.Y("rooms:Q", title="Rooms"),
            color=alt.Color(
                "line:N",
                title=None,
                scale=alt.Scale(domain=["rooms_on_books", "pace"], range=["#2ca02c", "#7f7f7f"]),
                legend=alt.Legend(
                    orient="top-right",
                    labelExpr="datum.label == 'pace' ? 'Pace curve' : 'Rooms on the books'",
                ),
            ),
        )
        .properties(height=170, title="Rooms on the books against the pace curve")
    )
    st.altair_chart(
        alt.vconcat(alt.layer(marks, rates), alt.layer(marks, pace)).resolve_scale(
            color="independent"
        ),
        width="stretch",
    )
    st.caption("Red marks are the stay dates the agent flagged today.")

    # ---- today's queue ------------------------------------------------------------------------
    queue = rows(
        "SELECT stays, causes, plan, value_text, reason, outcome, queued FROM queue "
        "WHERE as_of_day = ? AND hotel = ? ORDER BY position",
        day,
        key,
    )
    plans = queue.loc[queue["queued"]]
    held = queue.loc[~queue["queued"]]
    st.markdown("**Today's queue**")
    if plans.empty:
        st.markdown("No plan was queued today.")
    for plan in plans.itertuples():
        st.markdown(
            f"**{plan.outcome.capitalize()}:** {plan.plan} for {plan.stays}, {plan.value_text}. "
            f"{plan.reason}"
        )
    with st.expander(f"Held flags: {len(held)}", expanded=False):
        for flag in held.itertuples():
            st.markdown(f"{flag.stays}: {flag.causes}")

    # ---- the scorecard to date ----------------------------------------------------------------
    score = rows(
        "SELECT run, occupancy, adr, revpar, room_revenue, contribution FROM scorecard "
        "WHERE as_of_day = ? AND hotel = ?",
        day,
        key,
    ).set_index("run")
    st.markdown("**Scorecard to date, against the fixed-rate run** (bookings made through today)")
    columns = st.columns(5)
    columns[0].metric(
        "Occupancy",
        f"{score.at['agent', 'occupancy']:.1%}",
        f"{score.at['delta', 'occupancy']:+.1%}",
    )
    columns[1].metric(
        "ADR", f"${score.at['agent', 'adr']:,.2f}", f"{score.at['delta', 'adr']:+,.2f}"
    )
    columns[2].metric(
        "RevPAR", f"${score.at['agent', 'revpar']:,.2f}", f"{score.at['delta', 'revpar']:+,.2f}"
    )
    columns[3].metric(
        "Room revenue",
        f"${score.at['agent', 'room_revenue']:,.0f}",
        f"{score.at['delta', 'room_revenue']:+,.0f}",
    )
    columns[4].metric(
        "Contribution",
        f"${score.at['agent', 'contribution']:,.0f}",
        f"{score.at['delta', 'contribution']:+,.0f}",
    )


if __name__ == "__main__":
    main()
