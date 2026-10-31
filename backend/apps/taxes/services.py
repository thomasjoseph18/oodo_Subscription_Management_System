from django.db.models import Q

from common.money import ZERO, quantize

from .models import Tax


def taxes_for_products(product_ids):
    """Active taxes per product, loaded once for a whole document."""
    taxes = list(Tax.objects.filter(active=True).filter(Q(applies_to_all=True) | Q(products__in=product_ids)).distinct().prefetch_related("products"))
    return {
        product_id: [tax for tax in taxes if tax.applies_to_all or any(p.id == product_id for p in tax.products.all())]
        for product_id in product_ids
    }


def calculate_tax(tax, taxable, quantity):
    if tax.kind == "percent":
        return quantize(taxable * tax.rate / 100)
    return quantize(tax.rate * quantity)


def price_lines(document, lines, discounts=None):
    """Set line and document totals. Discounts come off before tax. `lines`
    are unsaved or saved line objects; `discounts` maps a line index to an
    amount. Returns each line's tax breakdown, by line index."""
    discounts = discounts or {}
    rules = taxes_for_products({line.product_id for line in lines})
    subtotal = discount_total = tax_total = ZERO
    breakdown = {}
    for index, line in enumerate(lines):
        gross = quantize(line.unit_price * line.quantity)
        discount = min(quantize(discounts.get(index, ZERO)), gross)
        taxable = gross - discount
        applied = [(tax, calculate_tax(tax, taxable, line.quantity)) for tax in rules[line.product_id]]
        line.discount_amount = discount
        line.tax_amount = sum((amount for _, amount in applied), ZERO)
        line.total = taxable + line.tax_amount
        breakdown[index] = applied
        subtotal += gross
        discount_total += discount
        tax_total += line.tax_amount
    document.subtotal = subtotal
    document.discount_total = discount_total
    document.tax_total = tax_total
    document.total = subtotal - discount_total + tax_total
    return breakdown
