"""text.py: the wording helpers, and the display strings the model request carries."""

import pytest

from hotel_market.text import (
    against_median,
    against_median_range,
    dollars,
    money_range,
    number,
    pace_text,
    percent_change,
    percent_change_range,
    percent_range,
    rooms,
    span,
    stay_range,
    tens_of_dollars,
    versus_holding,
)


def test_rates_read_to_the_dollar_and_estimates_to_the_nearest_ten():
    assert dollars(217.09) == "$217" and dollars(220.4) == "$220" and dollars(1234.5) == "$1,234"
    assert dollars(-120.4) == "-$120"
    assert tens_of_dollars(8052.54) == "$8,050" and tens_of_dollars(339.45) == "$340"
    assert tens_of_dollars(4.9) == "$0" and tens_of_dollars(-1867.45) == "-$1,870"


def test_a_signed_quantity_reads_as_a_phrase_with_its_direction_in_words():
    assert percent_change(0.15) == "up 15.0%" and percent_change(-0.2004) == "down 20.0%"
    assert percent_change(0.16965) == "up 17.0%" and percent_change(-0.0004) == "unchanged"
    assert against_median(-0.1465) == "14.6% below the median"
    assert against_median(0.025) == "2.5% above the median"
    assert against_median(0.0002) == "level with the median"
    assert versus_holding(339.45) == "$340 more than holding"
    assert versus_holding(-120.4) == "$120 less than holding"
    assert versus_holding(4.9) == "the same as holding"
    assert (
        pace_text(44.3) == "44 rooms ahead of pace" and pace_text(-44.6) == "45 rooms behind pace"
    )
    assert pace_text(1.2) == "1 room ahead of pace" and pace_text(0.3) == "on pace"


def test_a_range_is_one_phrase_and_the_single_value_when_both_ends_read_the_same():
    assert against_median_range([-0.1465, -0.107]) == "10.7% to 14.6% below the median"
    assert against_median_range([0.025, 0.0304]) == "2.5% to 3.0% above the median"
    assert against_median_range([-0.025, 0.0251]) == "2.5% below to 2.5% above the median"
    assert against_median_range([0.0, 0.025]) == "0.0% to 2.5% above the median"
    assert against_median_range([-0.0251, -0.0249]) == "2.5% below the median"
    assert against_median_range([-0.0003, 0.0004]) == "level with the median"
    assert percent_change_range([0.17, 0.216]) == "up 17.0% to 21.6%"
    assert percent_change_range([-0.216, -0.17]) == "down 17.0% to 21.6%"
    assert percent_change_range([-0.02, 0.03]) == "down 2.0% to up 3.0%"
    assert percent_change_range([-0.17, -0.0004]) == "down 0.0% to 17.0%"
    assert percent_change_range([0.15, 0.1504]) == "up 15.0%"
    assert span([45, 48], str) == "45 to 48" and span([46, 46], str) == "46"
    assert span([1.2, 1.8], number) == "1.2 to 1.8" and span([1.5, 1.5], number) == "1.5"
    assert money_range([242.0, 231.0]) == "$231 to $242"


def test_rooms_read_to_the_room_and_an_elasticity_with_up_to_two_decimals():
    assert rooms(1188) == "1,188" and rooms(963.1) == "963" and rooms(428.4) == "428"
    assert number(1.5) == "1.5" and number(1.62) == "1.62" and number(1.0) == "1"
    assert number(0.21) == "0.21" and number(0.004) == "0"


@pytest.mark.parametrize(
    "helper, values, expected",
    [
        (money_range, [220.0, 242.0], "$220 to $242"),
        (money_range, [220.0, 220.4], "$220"),
        (percent_range, [0.17, 0.22], "+17% to +22%"),
        (percent_range, [-0.146, -0.107], "-15% to -11%"),
    ],
)
def test_the_report_ranges_round_to_the_dollar_and_the_whole_percent(helper, values, expected):
    assert helper(values) == expected


def test_stay_wording():
    assert stay_range(46, 46) == "stay date 46" and stay_range(45, 48) == "stay dates 45 to 48"
