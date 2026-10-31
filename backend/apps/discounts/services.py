"""Discount rules are added in the next step. Until then no discount applies,
and invoices are priced with this interface already in place."""


def preview(lines, on):
    """Amount per line index for quotes. Uses nothing up."""
    return {}


def apply_to_invoice(invoice, lines, on):
    """Amount per line index for an invoice, reserving one use of the discount."""
    return {}


def release(invoice):
    """Give back the use held by a cancelled invoice."""
    return None
