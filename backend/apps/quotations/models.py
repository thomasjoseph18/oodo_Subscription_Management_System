from django.db import models

from apps.customers.models import Customer
from apps.plans.models import PaymentTerm, Plan
from apps.products.models import Product, ProductVariant
from apps.taxes.models import PricedDocument, PricedLine
from common.models import SoftDeleteModel


class QuotationTemplate(SoftDeleteModel):
    name = models.CharField(max_length=200)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="templates")
    payment_term = models.ForeignKey(PaymentTerm, null=True, blank=True, on_delete=models.SET_NULL)
    validity_days = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ["name"]


class QuotationTemplateLine(models.Model):
    template = models.ForeignKey(QuotationTemplate, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    quantity = models.PositiveIntegerField(default=1)


class Quotation(PricedDocument):
    STATUSES = [(s, s.title()) for s in ("draft", "sent", "accepted", "rejected", "expired")]

    number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="quotations")
    template = models.ForeignKey(QuotationTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="quotations")
    payment_term = models.ForeignKey(PaymentTerm, null=True, blank=True, on_delete=models.SET_NULL)
    valid_until = models.DateField()
    status = models.CharField(max_length=10, choices=STATUSES, default="draft", db_index=True)

    class Meta:
        ordering = ["-id"]


class QuotationLine(PricedLine):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="lines")
