import calendar
from datetime import date, timedelta

DAILY = "daily"
WEEKLY = "weekly"
MONTHLY = "monthly"
YEARLY = "yearly"
INTERVALS = [(DAILY, "Daily"), (WEEKLY, "Weekly"), (MONTHLY, "Monthly"), (YEARLY, "Yearly")]


def _add_months(anchor: date, months: int) -> date:
    index = anchor.year * 12 + (anchor.month - 1) + months
    year, month = index // 12, index % 12 + 1
    return date(year, month, min(anchor.day, calendar.monthrange(year, month)[1]))


def period_start(anchor: date, interval: str, n: int) -> date:
    """Start of the nth period, always counted from the anchor so that a
    31 Jan start gives 28 Feb then 31 Mar, not 28 Mar."""
    if interval == DAILY:
        return anchor + timedelta(days=n)
    if interval == WEEKLY:
        return anchor + timedelta(weeks=n)
    if interval == MONTHLY:
        return _add_months(anchor, n)
    if interval == YEARLY:
        return _add_months(anchor, 12 * n)
    raise ValueError(f"Unknown interval: {interval}")


def period_end(anchor: date, interval: str, n: int) -> date:
    return period_start(anchor, interval, n + 1) - timedelta(days=1)


def first_period_on_or_after(anchor: date, interval: str, day: date) -> int:
    """Lowest period number starting on or after the given day."""
    n = 0
    while period_start(anchor, interval, n) < day:
        n += 1
    return n


def mrr_factor(interval: str):
    """Multiplier that normalises one period's price to a month."""
    from decimal import Decimal

    return {
        DAILY: Decimal(365) / Decimal(12),
        WEEKLY: Decimal(52) / Decimal(12),
        MONTHLY: Decimal(1),
        YEARLY: Decimal(1) / Decimal(12),
    }[interval]
