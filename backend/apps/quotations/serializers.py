from rest_framework import serializers

from apps.products.models import Product, ProductVariant

from .models import Quotation, QuotationLine, QuotationTemplate, QuotationTemplateLine


class LineInputSerializer(serializers.Serializer):
    """Client input for a line. Prices are always set by the server."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all(), required=False, allow_null=True)
    quantity = serializers.IntegerField(min_value=1)


class QuotationLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationLine
        fields = ["id", "product", "variant", "description", "quantity", "unit_price", "discount_amount", "tax_amount", "total"]


class QuotationSerializer(serializers.ModelSerializer):
    lines = QuotationLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    payment_term_name = serializers.CharField(source="payment_term.name", default=None, read_only=True)
    subscription = serializers.IntegerField(source="subscription.id", default=None, read_only=True)

    class Meta:
        model = Quotation
        fields = [
            "id", "number", "customer", "customer_name", "plan", "plan_name", "template", "payment_term", "payment_term_name",
            "valid_until", "status", "subscription", "lines", "subtotal", "discount_total", "tax_total", "total", "created_at",
        ]


class QuotationCreateSerializer(serializers.ModelSerializer):
    lines = LineInputSerializer(many=True, required=False)

    class Meta:
        model = Quotation
        fields = ["customer", "plan", "template", "payment_term", "lines"]
        extra_kwargs = {"plan": {"required": False, "allow_null": True}}


class TemplateLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationTemplateLine
        fields = ["id", "product", "variant", "quantity"]


class QuotationTemplateSerializer(serializers.ModelSerializer):
    lines = TemplateLineSerializer(many=True, required=False)
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = QuotationTemplate
        fields = ["id", "name", "plan", "plan_name", "payment_term", "validity_days", "lines"]

    def create(self, validated_data):
        lines = validated_data.pop("lines", [])
        template = QuotationTemplate.objects.create(**validated_data)
        QuotationTemplateLine.objects.bulk_create(QuotationTemplateLine(template=template, **line) for line in lines)
        return template

    def update(self, instance, validated_data):
        lines = validated_data.pop("lines", None)
        instance = super().update(instance, validated_data)
        if lines is not None:
            instance.lines.all().delete()
            QuotationTemplateLine.objects.bulk_create(QuotationTemplateLine(template=instance, **line) for line in lines)
        return instance
