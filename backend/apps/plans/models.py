from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.products.models import Product
from common.billing_dates import INTERVALS
from common.models import SoftDeleteModel


class PaymentTerm(SoftDeleteModel):
    name = models.CharField(max_length=100)
    days = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["days"]

    def __str__(self):
        return self.name


class Plan(SoftDeleteModel):
    STATUSES = [("active", "Active"), ("inactive", "Inactive")]

    name = models.CharField(max_length=200, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="plans")
    price = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    interval = models.CharField(max_length=10, choices=INTERVALS, db_index=True)
    min_quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    available_from = models.DateField()
    available_to = models.DateField(null=True, blank=True)
    auto_close = models.BooleanField(default=False)
    can_close_early = models.BooleanField(default=True)
    can_pause = models.BooleanField(default=True)
    can_renew = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUSES, default="active", db_index=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(available_to__isnull=True) | Q(available_to__gte=F("available_from")),
                name="plan_available_dates_in_order",
            ),
        ]

    def __str__(self):
        return self.name

    def is_available(self, on):
        if self.status != "active" or on < self.available_from:
            return False
        return self.available_to is None or on <= self.available_to
