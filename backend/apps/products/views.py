from rest_framework import serializers

from common.permissions import AdminWriteTeamRead
from common.viewsets import AuditedModelViewSet

from .models import Product, ProductVariant


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "product_type", "sales_price", "cost_price", "notes", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class VariantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "product", "product_name", "name", "extra_price"]
        validators = []

    def validate(self, attrs):
        product = attrs.get("product") or self.instance.product
        name = attrs.get("name") or self.instance.name
        clash = ProductVariant.objects.filter(product=product, name=name)
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError({"name": ["This product already has a variant with that name."]})
        return attrs


class ProductViewSet(AuditedModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AdminWriteTeamRead]
    search_fields = ["name", "notes"]
    ordering_fields = ["name", "product_type", "sales_price", "cost_price", "status"]
    filterset_fields = ["status", "product_type"]


class VariantViewSet(AuditedModelViewSet):
    queryset = ProductVariant.objects.select_related("product")
    serializer_class = VariantSerializer
    permission_classes = [AdminWriteTeamRead]
    search_fields = ["name", "product__name"]
    ordering_fields = ["name", "extra_price"]
    filterset_fields = ["product"]
