from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.customers.models import Customer
from apps.invoices.models import Invoice
from common.models import TimeStampedModel


class Payment(TimeStampedModel):
    METHODS = [
        ("cash", "Cash"), ("bank_transfer", "Bank transfer"), ("upi", "UPI"), ("debit_card", "Debit card"),
        ("credit_card", "Credit card"), ("online_gateway", "Online payment gateway"),
    ]
    STATUSES = [("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")]

    reference = models.CharField(max_length=30, unique=True, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=20, choices=METHODS, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_on = models.DateField(db_index=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default="completed", db_index=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    gateway_order_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    gateway_payment_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    gateway_invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    invoices = models.ManyToManyField(Invoice, through="PaymentAllocation", related_name="payments")

    class Meta:
        ordering = ["-paid_on", "-id"]
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive")]


class PaymentAllocation(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="allocations")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="allocations")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["payment", "invoice"], name="one_allocation_per_payment_invoice"),
            models.CheckConstraint(condition=Q(amount__gt=0), name="allocation_amount_positive"),
        ]


class GatewayEvent(models.Model):
    """Every webhook seen, keyed on Razorpay's event id, so replays do nothing."""

    event_id = models.CharField(max_length=100, unique=True)
    event = models.CharField(max_length=60)
    payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)
