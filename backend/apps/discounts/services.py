from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from apps.notifications.services import notify
from common.money import ZERO, quantize

from .models import Discount, DiscountRedemption


def _gross(line):
    return quantize(line.unit_price * line.quantity)


def _amounts(discount, lines):
    """Amount per line index, or {} when the lines don't qualify. All checks
    use server prices, so a client can't talk its way into a discount."""
    product_ids = {product.id for product in discount.products.all()}
    matching = [i for i, line in enumerate(lines) if discount.scope == "subscription" or line.product_id in product_ids]
    if not matching:
        return {}
    base = sum((_gross(lines[i]) for i in matching), ZERO)
    quantity = sum(lines[i].quantity for i in matching)
    if base <= 0 or base < discount.min_purchase or quantity < discount.min_quantity:
        return {}
    total = quantize(base * discount.value / 100) if discount.kind == "percent" else min(discount.value, base)
    amounts, spread = {}, ZERO
    for i in matching[:-1]:
        amounts[i] = quantize(total * _gross(lines[i]) / base)
        spread += amounts[i]
    amounts[matching[-1]] = total - spread
    return amounts


def _best(lines, on, discounts):
    """One discount per document, the largest that qualifies. No stacking."""
    best, best_amounts, best_total = None, {}, ZERO
    for discount in discounts:
        if not discount.is_live(on):
            continue
        amounts = _amounts(discount, lines)
        total = sum(amounts.values(), ZERO)
        if total > best_total:
            best, best_amounts, best_total = discount, amounts, total
    return best, best_amounts


def _live_candidates(on):
    return Discount.objects.filter(Q(ends_on__isnull=True) | Q(ends_on__gte=on), active=True, starts_on__lte=on)


def preview(lines, on):
    """Amount per line index for quotes. Uses nothing up."""
    return _best(lines, on, _live_candidates(on).prefetch_related("products"))[1]


def apply_to_invoice(invoice, lines, on):
    """Amount per line index for an invoice, reserving one use of the discount.
    Rows are locked, so two invoices can't take the last remaining use."""
    best, amounts = _best(lines, on, _live_candidates(on).select_for_update().prefetch_related("products"))
    if best is None:
        return {}
    Discount.objects.filter(pk=best.pk).update(times_used=F("times_used") + 1)
    DiscountRedemption.objects.create(discount=best, invoice=invoice, amount=sum(amounts.values(), Decimal("0.00")))
    return amounts


@transaction.atomic
def release(invoice):
    """Give back the use held by a cancelled invoice."""
    redemption = DiscountRedemption.objects.filter(invoice=invoice).first()
    if redemption:
        Discount.objects.filter(pk=redemption.discount_id).update(times_used=F("times_used") - 1)
        redemption.delete()


def notify_expiring(today=None):
    today = today or timezone.localdate()
    ending = list(Discount.objects.filter(active=True, ends_on=today))
    admins = get_user_model().objects.filter(role="admin", is_active=True)
    for discount in ending:
        for admin in admins:
            notify(admin, "discount_expiry", f"Discount {discount.name} ends today", email=False)
    return len(ending)
