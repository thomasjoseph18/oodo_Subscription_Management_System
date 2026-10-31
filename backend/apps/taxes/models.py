from django.core.validators import MinValueValidator
from django.db import models

from apps.products.models import Product, ProductVariant
from common.models import SoftDeleteModel, TimeStampedModel


class Tax(SoftDeleteModel):
    KINDS = [("percent", "Percentage"), ("fixed", "Fixed amount per unit")]

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=KINDS, default="percent")
    rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True, db_index=True)
    applies_to_all = models.BooleanField(default=True)
    products = models.ManyToManyField(Product, blank=True, related_name="taxes")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PricedDocument(TimeStampedModel):
    """Totals shared by quotations, subscriptions and invoices."""

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        abstract = True


class PricedLine(models.Model):
    """Values are copied onto the line so later catalogue edits can't rewrite history."""

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        abstract = True
        ordering = ["id"]
