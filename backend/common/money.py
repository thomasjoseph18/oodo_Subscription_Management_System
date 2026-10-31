from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def quantize(value):
    """Round a monetary value half-up to two decimals."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def to_paise(value):
    return int(quantize(value) * 100)
