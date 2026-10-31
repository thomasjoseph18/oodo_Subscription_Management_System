from django.utils import timezone
from rest_framework import serializers

from .models import BillingRun, BillingSettings, Invoice, InvoiceLine


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ["id", "product", "description", "quantity", "unit_price", "discount_amount", "tax_amount", "total"]


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    subscription_number = serializers.CharField(source="subscription.number", read_only=True)
    outstanding = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    payment_state = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "number", "customer", "customer_name", "subscription", "subscription_number", "invoice_date", "due_date",
            "period_start", "period_end", "subtotal", "discount_total", "tax_total", "total", "amount_paid", "outstanding",
            "status", "payment_state", "sent_at",
        ]

    def get_payment_state(self, obj):
        return obj.payment_state(timezone.localdate())


class InvoiceDetailSerializer(InvoiceSerializer):
    lines = InvoiceLineSerializer(many=True, read_only=True)

    class Meta(InvoiceSerializer.Meta):
        fields = InvoiceSerializer.Meta.fields + ["lines"]


class BillingRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingRun
        fields = ["id", "run_date", "started_at", "finished_at", "subscriptions_seen", "invoices_created", "failures"]


class BillingSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingSettings
        fields = ["auto_confirm_invoices"]
