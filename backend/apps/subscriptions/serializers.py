from rest_framework import serializers

from apps.quotations.serializers import LineInputSerializer

from . import services
from .models import PlanChangeRequest, Subscription, SubscriptionEvent, SubscriptionLine


class SubscriptionLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionLine
        fields = ["id", "product", "variant", "description", "quantity", "unit_price", "discount_amount", "tax_amount", "total"]


class SubscriptionSerializer(serializers.ModelSerializer):
    lines = SubscriptionLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    interval = serializers.CharField(source="plan.interval", read_only=True)
    payment_term_name = serializers.CharField(source="payment_term.name", default=None, read_only=True)
    allowed_actions = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id", "number", "customer", "customer_name", "plan", "plan_name", "interval", "start_date", "expiry_date",
            "payment_term", "payment_term_name", "status", "next_billing_date", "allowed_actions", "lines",
            "subtotal", "discount_total", "tax_total", "total", "renewed_from", "created_at",
        ]

    def get_allowed_actions(self, obj):
        return services.allowed_actions(obj)


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    lines = LineInputSerializer(many=True, required=False)

    class Meta:
        model = Subscription
        fields = ["customer", "plan", "start_date", "expiry_date", "payment_term", "lines"]


class SubscriptionEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", default=None, read_only=True)

    class Meta:
        model = SubscriptionEvent
        fields = ["id", "message", "from_status", "to_status", "actor_email", "created_at"]


class PlanChangeSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = PlanChangeRequest
        fields = ["id", "subscription", "plan", "plan_name", "status", "created_at"]
        read_only_fields = ["subscription", "status"]
