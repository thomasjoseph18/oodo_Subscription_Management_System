from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit_logs.services import record
from apps.invoices.models import Invoice
from apps.notifications.services import notify
from common import razorpay_client
from common.exceptions import BusinessRuleError
from common.money import to_paise

from .models import GatewayEvent, Payment, PaymentAllocation


def _allocate(payment, invoice, amount):
    """`invoice` must already be locked by the caller."""
    PaymentAllocation.objects.create(payment=payment, invoice=invoice, amount=amount)
    invoice.amount_paid += amount
    if invoice.amount_paid >= invoice.total:
        invoice.status = "paid"
    invoice.save(update_fields=["amount_paid", "status", "updated_at"])


def _lock_payable(invoice_id):
    invoice = Invoice.objects.select_for_update(of=("self",)).select_related("customer").get(pk=invoice_id)
    if invoice.status != "confirmed":
        raise BusinessRuleError(f"A {invoice.status} invoice can't take a payment.", "invoice_not_payable")
    return invoice


def _finish(payment):
    payment.reference = payment.reference or f"PAY-{payment.pk:06d}"
    payment.save()
    notify(payment.customer.user, "payment_confirmed", f"Payment {payment.reference} received", f"Thank you. We received ₹{payment.amount}.")


@transaction.atomic
def record_payment(user, allocations, method, paid_on, notes=""):
    """One payment split across one or more invoices of the same customer.
    `allocations` is a list of (invoice id, amount). Invoices are locked in id
    order, so two payments can't deadlock or overpay together."""
    allocations = sorted(allocations, key=lambda item: item[0])
    invoices = [(_lock_payable(invoice_id), amount) for invoice_id, amount in allocations]
    if len({invoice.customer_id for invoice, _ in invoices}) != 1:
        raise BusinessRuleError("A payment can only cover one customer's invoices.", "mixed_customers")
    for invoice, amount in invoices:
        if amount > invoice.outstanding:
            raise BusinessRuleError(f"{invoice.number} has only ₹{invoice.outstanding} outstanding.", "overpayment")
    payment = Payment.objects.create(
        customer=invoices[0][0].customer, method=method, amount=sum((amount for _, amount in invoices), Decimal("0.00")),
        paid_on=paid_on, notes=notes, recorded_by=user,
    )
    for invoice, amount in invoices:
        _allocate(payment, invoice, amount)
    _finish(payment)
    record(user, "record_payment", payment, after={"amount": str(payment.amount), "method": method})
    return payment


@transaction.atomic
def create_gateway_order(user, invoice_id):
    invoice = _lock_payable(invoice_id)
    amount = invoice.outstanding
    order = razorpay_client.create_order(to_paise(amount), invoice.number, {"invoice_id": str(invoice.id)})
    payment = Payment.objects.create(
        customer=invoice.customer, method="online_gateway", amount=amount, paid_on=timezone.localdate(),
        status="pending", recorded_by=user, gateway_order_id=order["id"], gateway_invoice=invoice,
    )
    return {"key": razorpay_client.settings.RAZORPAY_KEY_ID, "order_id": order["id"], "amount": to_paise(amount), "payment": payment.id}


@transaction.atomic
def settle_gateway_payment(order_id, gateway_payment_id, amount_paise=None):
    """Called by checkout and by the webhook. Whichever arrives first settles
    the payment; the other finds it completed and does nothing."""
    payment = Payment.objects.select_for_update(of=("self",)).select_related("customer__user").filter(gateway_order_id=order_id).first()
    if payment is None:
        raise BusinessRuleError("Unknown payment order.", "unknown_order")
    if payment.status == "completed":
        return payment
    if amount_paise is not None and amount_paise != to_paise(payment.amount):
        raise BusinessRuleError("The amount paid doesn't match the order.", "amount_mismatch")
    invoice = Invoice.objects.select_for_update().get(pk=payment.gateway_invoice_id)
    amount = min(payment.amount, invoice.outstanding)
    payment.status = "completed"
    payment.gateway_payment_id = gateway_payment_id
    if amount > 0 and invoice.status == "confirmed":
        _allocate(payment, invoice, amount)
    if amount < payment.amount:
        payment.notes += f". ₹{payment.amount - amount} needs refunding: the invoice was paid another way first."
    _finish(payment)
    return payment


@transaction.atomic
def fail_gateway_payment(order_id, reason=""):
    payment = Payment.objects.select_for_update(of=("self",)).select_related("customer__user").filter(gateway_order_id=order_id).first()
    if payment is None or payment.status == "completed":
        return
    payment.status = "failed"
    payment.notes += f". Failed: {reason}" if reason else ". Failed"
    payment.save()
    notify(payment.customer.user, "payment_failed", "Your payment didn't go through", "Please try again.")


def verify_checkout(order_id, payment_id, signature):
    if not razorpay_client.verify_checkout_signature(order_id, payment_id, signature):
        raise BusinessRuleError("The payment signature is invalid.", "invalid_signature")
    return settle_gateway_payment(order_id, payment_id)


def handle_webhook(event_id, payload):
    """Apply one verified webhook. A repeated event id is ignored."""
    try:
        with transaction.atomic():
            GatewayEvent.objects.create(event_id=event_id, event=payload.get("event", ""), payload=payload)
    except IntegrityError:
        return False
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = entity.get("order_id")
    if payload.get("event") == "payment.captured":
        settle_gateway_payment(order_id, entity.get("id"), entity.get("amount"))
    elif payload.get("event") == "payment.failed":
        fail_gateway_payment(order_id, entity.get("error_description", ""))
    return True
