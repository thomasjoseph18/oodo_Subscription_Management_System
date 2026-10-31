from django.conf import settings
from django.db import models

from common.models import SoftDeleteModel


class Customer(SoftDeleteModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="customer")
    name = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    company = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    gst_number = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField(blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_customers")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
