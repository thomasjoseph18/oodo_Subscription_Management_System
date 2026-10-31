from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit_logs.services import record
from apps.notifications.services import notify
from apps.plans.services import ensure_available, ensure_min_quantity, line_unit_price
from apps.taxes.services import price_lines
from common.exceptions import BusinessRuleError

from .models import Quotation, QuotationLine


def build_lines(plan, raw_lines, line_model, **parent):
    """Turn product, variant and quantity input into priced line objects.
    With no lines given, a single line for the plan's own product is used."""
    raw_lines = raw_lines or [{"product": plan.product, "variant": None, "quantity": plan.min_quantity}]
    ensure_min_quantity(plan, raw_lines)
    lines = []
    for raw in raw_lines:
        product, variant = raw["product"], raw.get("variant")
        if variant and variant.product_id != product.id:
            raise BusinessRuleError(f"{variant.name} isn't a variant of {product.name}.", "invalid_variant")
        name = f"{product.name} ({variant.name})" if variant else product.name
        lines.append(
            line_model(
                product=product, variant=variant, description=name, quantity=raw["quantity"],
                unit_price=line_unit_price(product, variant, plan), **parent,
            )
        )
    return lines


@transaction.atomic
def create_quotation(user, customer, plan=None, template=None, payment_term=None, lines=None):
    if template:
        plan = plan or template.plan
        payment_term = payment_term or template.payment_term
        lines = lines or [{"product": line.product, "variant": line.variant, "quantity": line.quantity} for line in template.lines.all()]
    if plan is None:
        raise BusinessRuleError("Choose a plan or a template.", "plan_required")
    today = timezone.localdate()
    ensure_available(plan, today)
    validity = template.validity_days if template else 30
    quotation = Quotation.objects.create(
        customer=customer, plan=plan, template=template, payment_term=payment_term, valid_until=today + timedelta(days=validity),
    )
    built = build_lines(plan, lines, QuotationLine, quotation=quotation)
    price_lines(quotation, built)
    QuotationLine.objects.bulk_create(built)
    quotation.number = f"QUO-{quotation.pk:06d}"
    quotation.save()
    record(user, "create", quotation)
    return quotation


def _move(user, quotation, allowed_from, status):
    if quotation.status not in allowed_from:
        raise BusinessRuleError(f"A {quotation.status} quotation can't become {status}.", "invalid_transition")
    quotation.status = status
    quotation.save(update_fields=["status", "updated_at"])
    record(user, status, quotation)
    return quotation


@transaction.atomic
def send(user, quotation):
    _move(user, quotation, {"draft"}, "sent")
    notify(quotation.customer.user, "quotation_sent", f"Quotation {quotation.number}", f"Valid until {quotation.valid_until}.")
    return quotation


@transaction.atomic
def accept(user, quotation):
    if quotation.valid_until < timezone.localdate():
        raise BusinessRuleError("This quotation has expired.", "quotation_expired")
    return _move(user, quotation, {"sent"}, "accepted")


@transaction.atomic
def reject(user, quotation):
    return _move(user, quotation, {"sent"}, "rejected")


def expire_overdue(today=None):
    today = today or timezone.localdate()
    expiring = Quotation.objects.filter(status="sent", valid_until__lt=today).select_related("customer__user")
    count = 0
    for quotation in expiring:
        with transaction.atomic():
            _move(None, quotation, {"sent"}, "expired")
            notify(quotation.customer.user, "quotation_expired", f"Quotation {quotation.number} has expired")
        count += 1
    return count
