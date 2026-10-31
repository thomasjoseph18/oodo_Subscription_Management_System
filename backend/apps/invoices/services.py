from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit_logs.services import record
from apps.discounts import services as discounts
from apps.notifications.services import notify
from apps.subscriptions.models import Subscription
from apps.taxes.services import price_lines
from common.billing_dates import period_end, period_start
from common.exceptions import BusinessRuleError

from .models import BillingRun, BillingSettings, Invoice, InvoiceLine, InvoiceLineTax


def _build_invoice(subscription, n, today):
    interval = subscription.plan.interval
    start = period_start(subscription.start_date, interval, n)
    invoice = Invoice.objects.create(
        customer=subscription.customer, subscription=subscription, invoice_date=today,
        due_date=today + timedelta(days=subscription.payment_term.days if subscription.payment_term else 0),
        period_start=start, period_end=period_end(subscription.start_date, interval, n),
    )
    lines = [
        InvoiceLine(invoice=invoice, product=line.product, variant=line.variant, description=line.description, quantity=line.quantity, unit_price=line.unit_price)
        for line in subscription.lines.select_related("product")
    ]
    breakdown = price_lines(invoice, lines, discounts.apply_to_invoice(invoice, lines, today))
    InvoiceLine.objects.bulk_create(lines)
    InvoiceLineTax.objects.bulk_create(
        InvoiceLineTax(line=lines[index], name=tax.name, rate=tax.rate, kind=tax.kind, amount=amount)
        for index, applied in breakdown.items() for tax, amount in applied
    )
    invoice.number = f"INV-{invoice.pk:06d}"
    invoice.save()
    return invoice


def _bill_subscription(subscription_id, today, auto_confirm):
    """Bill every due period of one subscription, oldest first. The cursor
    moves in the same transaction as the invoice, so a crash can neither
    skip a period nor repeat one. SKIP LOCKED leaves a row another worker
    is already billing."""
    created = 0
    with transaction.atomic():
        subscription = (
            Subscription.objects.select_for_update(skip_locked=True, of=("self",))
            .select_related("plan", "customer__user", "payment_term")
            .filter(pk=subscription_id, status="active", next_billing_date__lte=today)
            .first()
        )
        if subscription is None:
            return 0
        interval = subscription.plan.interval
        while subscription.next_billing_date and subscription.next_billing_date <= today:
            if subscription.expiry_date and subscription.next_billing_date > subscription.expiry_date:
                subscription.next_billing_date = None
                break
            invoice = _build_invoice(subscription, subscription.next_period, today)
            created += 1
            if auto_confirm:
                confirm_invoice(None, invoice)
            subscription.next_period += 1
            subscription.next_billing_date = period_start(subscription.start_date, interval, subscription.next_period)
        subscription.save(update_fields=["next_period", "next_billing_date", "updated_at"])
    return created


def run_billing(today=None):
    today = today or timezone.localdate()
    auto_confirm = BillingSettings.load().auto_confirm_invoices
    run = BillingRun.objects.create(run_date=today)
    due = list(Subscription.objects.filter(status="active", next_billing_date__lte=today).values_list("id", flat=True))
    run.subscriptions_seen = len(due)
    for subscription_id in due:
        try:
            run.invoices_created += _bill_subscription(subscription_id, today, auto_confirm)
        except IntegrityError:
            # The unique constraint fired: that period is already billed.
            run.failures.append({"subscription": subscription_id, "error": "period already billed"})
        except Exception as error:  # One bad subscription must not stop the rest.
            run.failures.append({"subscription": subscription_id, "error": str(error)})
    run.finished_at = timezone.now()
    run.save()
    return run


@transaction.atomic
def confirm_invoice(user, invoice):
    if invoice.status != "draft":
        raise BusinessRuleError(f"A {invoice.status} invoice can't be confirmed.", "invalid_transition")
    invoice.status = "confirmed" if invoice.total > 0 else "paid"
    invoice.save(update_fields=["status", "updated_at"])
    record(user, "confirm", invoice)
    notify(invoice.customer.user, "invoice_generated", f"Invoice {invoice.number}", f"Total ₹{invoice.total}, due {invoice.due_date}.", email=False)
    return invoice


@transaction.atomic
def cancel_invoice(user, invoice):
    invoice = Invoice.objects.select_for_update(of=("self",)).get(pk=invoice.pk)
    if invoice.status not in ("draft", "confirmed"):
        raise BusinessRuleError(f"A {invoice.status} invoice can't be cancelled.", "invalid_transition")
    if invoice.amount_paid > 0:
        raise BusinessRuleError("This invoice has payments against it.", "has_payments")
    invoice.status = "cancelled"
    invoice.save(update_fields=["status", "updated_at"])
    discounts.release(invoice)
    record(user, "cancel", invoice)
    return invoice


@transaction.atomic
def reissue_invoice(user, cancelled):
    """Bill a cancelled invoice's period again."""
    if cancelled.status != "cancelled":
        raise BusinessRuleError("Only a cancelled invoice can be reissued.", "invalid_transition")
    subscription = cancelled.subscription
    interval = subscription.plan.interval
    n = 0
    while period_start(subscription.start_date, interval, n) < cancelled.period_start:
        n += 1
    try:
        with transaction.atomic():
            invoice = _build_invoice(subscription, n, timezone.localdate())
    except IntegrityError as error:
        raise BusinessRuleError("This period already has an invoice.", "already_billed") from error
    record(user, "reissue", invoice, metadata_from=cancelled.number)
    return invoice


def send_overdue_reminders(today=None):
    today = today or timezone.localdate()
    overdue = Invoice.objects.filter(status="confirmed", due_date=today - timedelta(days=1)).select_related("customer__user")
    for invoice in overdue:
        notify(invoice.customer.user, "invoice_overdue", f"Invoice {invoice.number} is overdue", f"₹{invoice.outstanding} is still outstanding.")
    return len(overdue)
