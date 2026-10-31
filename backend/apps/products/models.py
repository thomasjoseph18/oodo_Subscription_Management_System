from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from common.models import SoftDeleteModel


class Product(SoftDeleteModel):
    TYPES = [("software", "Software"), ("add_on", "Add-on"), ("service", "Service")]
    STATUSES = [("active", "Active"), ("archived", "Archived")]

    name = models.CharField(max_length=200, db_index=True)
    product_type = models.CharField(max_length=20, choices=TYPES)
    sales_price = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default="active", db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductVariant(SoftDeleteModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="variants")
    name = models.CharField(max_length=100)
    extra_price = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    class Meta:
        ordering = ["product_id", "name"]
        constraints = [
            models.UniqueConstraint(fields=["product", "name"], condition=Q(deleted_at__isnull=True), name="unique_live_variant_name"),
        ]

    def __str__(self):
        return f"{self.product.name} ({self.name})"
