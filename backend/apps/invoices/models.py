from django.db import models
from django.db.models import F, Q

from apps.customers.models import Customer
from apps.subscriptions.models import Subscription
from apps.taxes.models import PricedDocument, PricedLine


class BillingSettings(models.Model):
    """Single row of billing options the admin can change."""

    auto_confirm_invoices = models.BooleanField(default=True)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]


class Invoice(PricedDocument):
    STATUSES = [(s, s.title()) for s in ("draft", "confirmed", "paid", "cancelled")]

    number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="invoices")
    subscription = models.ForeignKey(Subscription, on_delete=models.PROTECT, related_name="invoices")
    invoice_date = models.DateField(db_index=True)
    due_date = models.DateField(db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUSES, default="draft", db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        constraints = [
            # The database itself refuses to bill a period twice. A cancelled
            # invoice frees its period so that it can be reissued.
            models.UniqueConstraint(
                fields=["subscription", "period_start"], condition=~Q(status="cancelled"), name="one_live_invoice_per_period",
            ),
            models.CheckConstraint(condition=Q(amount_paid__gte=0) & Q(amount_paid__lte=F("total")), name="amount_paid_within_total"),
        ]
        indexes = [models.Index(fields=["status", "due_date"])]

    @property
    def outstanding(self):
        return self.total - self.amount_paid

    def payment_state(self, today):
        if self.status == "paid":
            return "paid"
        if self.status == "confirmed" and self.due_date < today:
            return "overdue"
        return "partial" if self.amount_paid > 0 else "unpaid"


class InvoiceLine(PricedLine):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")


class InvoiceLineTax(models.Model):
    """The tax rule as it stood on the invoice date."""

    line = models.ForeignKey(InvoiceLine, on_delete=models.CASCADE, related_name="taxes")
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    kind = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=14, decimal_places=2)


class BillingRun(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    run_date = models.DateField()
    subscriptions_seen = models.PositiveIntegerField(default=0)
    invoices_created = models.PositiveIntegerField(default=0)
    failures = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-id"]
