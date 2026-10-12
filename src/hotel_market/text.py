"""text.py

Wording shared by the template reasons and the printed reports, so that a
number reads the same wherever it appears, and the display strings the model
request carries in place of every figure, so that the model quotes figures the
way code wrote them: dollars to the dollar for a rate, to the nearest $10 for
an estimate, percentages to one decimal, rooms to the room. A signed quantity
reads as a phrase with a direction word and no sign ("14.6% below the median",
"up 15.0%", "44 rooms ahead of pace", "$120 less than holding"), and a range
as one phrase ("10.7% to 14.6% below the median", "up 17.0% to 21.6%", "2.5%
below to 2.5% above the median", "$220 to $242"), the single value when both
ends read the same, so that the model copies a phrase that already reads
correctly.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable


def stay_range(first_stay: int, last_stay: int) -> str:
    """Either "stay date 46" or "stay dates 45 to 48"."""
    if first_stay == last_stay:
        return f"stay date {first_stay}"
    return f"stay dates {first_stay} to {last_stay}"


def money_range(values: Iterable[float]) -> str:
    """Either "$220", or "$220 to $242" when the values differ once rounded to the dollar."""
    return span(values, dollars)


def percent_range(fractions: Iterable[float]) -> str:
    """Either "+17%" or "+17% to +22%", from fractions such as 0.17."""
    low, high = _bounds(100 * fraction for fraction in fractions)
    if round(low) == round(high):
        return f"{low:+.0f}%"
    return f"{low:+.0f}% to {high:+.0f}%"


def pace_text(pace_gap: float) -> str:
    """ "45 rooms behind pace", "2 rooms ahead of pace", "1 room ahead of pace" or "on pace"."""
    count = round(abs(pace_gap))
    if count == 0:
        return "on pace"
    side = "ahead of" if pace_gap > 0 else "behind"
    return f"{count:,} {'room' if count == 1 else 'rooms'} {side} pace"


def capitalize_first(text: str) -> str:
    """Upper-case the first letter and leave the rest alone, unlike str.capitalize()."""
    return text[:1].upper() + text[1:]


# ---- display strings: how a figure reads in the model request -------------


def dollars(value: float) -> str:
    """ "$217" to the dollar, for a rate; a negative amount reads "-$120"."""
    return _dollars(round(value))


def tens_of_dollars(value: float) -> str:
    """ "$8,050" to the nearest $10, for an estimate."""
    return _dollars(10 * round(value / 10))


def _dollars(amount: int) -> str:
    return f"-${-amount:,}" if amount < 0 else f"${amount:,}"


def percent_change(fraction: float) -> str:
    """ "up 15.0%", "down 20.0%" or "unchanged", to one decimal, from a fraction such as 0.15."""
    return _change(_percent_value(fraction))


def percent_change_range(fractions: Iterable[float]) -> str:
    """One phrase for a range of changes: "up 17.0% to 21.6%", "down 17.0% to 21.6%" (the
    smaller change first), "down 2.0% to up 3.0%", or the single phrase when both ends
    read the same."""
    low, high = _bounds(_percent_value(fraction) for fraction in fractions)
    if low == high:
        return _change(high)
    if low >= 0:
        return f"up {low:.1f}% to {high:.1f}%"
    if high <= 0:
        return f"down {abs(high):.1f}% to {abs(low):.1f}%"
    return f"down {abs(low):.1f}% to up {high:.1f}%"


def against_median(fraction: float) -> str:
    """ "14.6% below the median", "2.5% above the median" or "level with the median"."""
    return _position(_percent_value(fraction))


def against_median_range(fractions: Iterable[float]) -> str:
    """One phrase for a range of positions: "10.7% to 14.6% below the median" (the smaller
    gap first), "2.5% to 3.0% above the median", "2.5% below to 2.5% above the median",
    or the single phrase when both ends read the same."""
    low, high = _bounds(_percent_value(fraction) for fraction in fractions)
    if low == high:
        return _position(high)
    if low >= 0:
        return f"{low:.1f}% to {high:.1f}% above the median"
    if high <= 0:
        return f"{abs(high):.1f}% to {abs(low):.1f}% below the median"
    return f"{abs(low):.1f}% below to {high:.1f}% above the median"


def _percent_value(fraction: float) -> float:
    """A fraction as a percentage to one decimal; adding 0.0 turns -0.0 into 0.0."""
    return round(100 * fraction, 1) + 0.0


def _change(value: float) -> str:
    if value == 0:
        return "unchanged"
    return f"{'up' if value > 0 else 'down'} {abs(value):.1f}%"


def _position(value: float) -> str:
    if value == 0:
        return "level with the median"
    return f"{abs(value):.1f}% {'above' if value > 0 else 'below'} the median"


def versus_holding(amount: float) -> str:
    """ "$340 more than holding", "$120 less than holding" or "the same as holding", to
    the nearest $10, for an estimate against hold's."""
    tens = 10 * round(amount / 10)
    if tens == 0:
        return "the same as holding"
    return f"{_dollars(abs(tens))} {'more' if tens > 0 else 'less'} than holding"


def rooms(count: float) -> str:
    """ "1,188" to the room."""
    return f"{round(count):,}"


def number(value: float) -> str:
    """ "1.5", "0.21" or "1": up to two decimals, trailing zeros dropped, for an elasticity."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def span(values: Iterable[float], display: Callable[[float], str]) -> str:
    """A range as one phrase: each end as display writes it, "45 to 48" or "$220 to
    $242", or the single value when both ends read the same."""
    low, high = _bounds(values)
    lowest, highest = display(low), display(high)
    return lowest if lowest == highest else f"{lowest} to {highest}"


def _bounds(values: Iterable[float]) -> tuple[float, float]:
    values = list(values)
    return min(values), max(values)
