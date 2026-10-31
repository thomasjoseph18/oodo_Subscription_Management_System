from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.invoices.models import Invoice
from apps.products.models import Product
from common.models import SoftDeleteModel


class Discount(SoftDeleteModel):
    KINDS = [("percent", "Percentage"), ("fixed", "Fixed amount")]
    SCOPES = [("subscription", "Whole subscription"), ("product", "Specific products")]

    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=KINDS)
    value = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    scope = models.CharField(max_length=15, choices=SCOPES, default="subscription")
    products = models.ManyToManyField(Product, blank=True, related_name="discounts")
    min_purchase = models.DecimalField(max_digits=14, decimal_places=2, default=0, blank=True)
    min_quantity = models.PositiveIntegerField(default=0, blank=True)
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True, db_index=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(usage_limit__isnull=True) | Q(times_used__lte=F("usage_limit")), name="discount_within_usage_limit",
            ),
            models.CheckConstraint(condition=~Q(kind="percent") | Q(value__lte=100), name="discount_percent_at_most_100"),
        ]

    def is_live(self, on):
        if not self.active or on < self.starts_on or (self.ends_on and on > self.ends_on):
            return False
        return self.usage_limit is None or self.times_used < self.usage_limit


class DiscountRedemption(models.Model):
    discount = models.ForeignKey(Discount, on_delete=models.PROTECT, related_name="redemptions")
    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="redemption")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
