from django.conf import settings
from django.db import models

from apps.customers.models import Customer
from apps.plans.models import PaymentTerm, Plan
from apps.quotations.models import Quotation
from apps.taxes.models import PricedDocument, PricedLine


class Subscription(PricedDocument):
    STATUSES = [(s, s.title()) for s in ("draft", "quotation", "confirmed", "active", "paused", "renewed", "closed")]

    number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    payment_term = models.ForeignKey(PaymentTerm, null=True, blank=True, on_delete=models.SET_NULL)
    start_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUSES, default="draft", db_index=True)
    next_period = models.PositiveIntegerField(default=0)
    next_billing_date = models.DateField(null=True, blank=True, db_index=True)
    source_quotation = models.OneToOneField(Quotation, null=True, blank=True, on_delete=models.SET_NULL, related_name="subscription")
    renewed_from = models.OneToOneField("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="renewed_by")
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        indexes = [models.Index(fields=["status", "next_billing_date"])]

    def __str__(self):
        return self.number or f"Subscription {self.pk}"


class SubscriptionLine(PricedLine):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="lines")


class SubscriptionEvent(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    from_status = models.CharField(max_length=10, blank=True)
    to_status = models.CharField(max_length=10, blank=True)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]


class PlanChangeRequest(models.Model):
    STATUSES = [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")]

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="plan_changes")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="+")
    status = models.CharField(max_length=10, choices=STATUSES, default="pending", db_index=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
