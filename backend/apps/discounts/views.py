from rest_framework import serializers

from common.permissions import AdminWriteTeamRead
from common.viewsets import AuditedModelViewSet

from .models import Discount


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = [
            "id", "name", "kind", "value", "scope", "products", "min_purchase", "min_quantity", "starts_on", "ends_on",
            "usage_limit", "times_used", "active",
        ]
        read_only_fields = ["times_used"]

    def validate(self, attrs):
        get = lambda name: attrs.get(name, getattr(self.instance, name, None))
        if get("kind") == "percent" and get("value") is not None and get("value") > 100:
            raise serializers.ValidationError({"value": ["A percentage can't be more than 100."]})
        if get("ends_on") and get("starts_on") and get("ends_on") < get("starts_on"):
            raise serializers.ValidationError({"ends_on": ["This can't be before the start date."]})
        if get("scope") == "product" and "products" in attrs and not attrs["products"]:
            raise serializers.ValidationError({"products": ["Choose at least one product."]})
        for name in ("min_purchase", "min_quantity"):
            if name in attrs and attrs[name] is None:
                attrs[name] = 0
        return attrs


class DiscountViewSet(AuditedModelViewSet):
    queryset = Discount.objects.prefetch_related("products")
    serializer_class = DiscountSerializer
    permission_classes = [AdminWriteTeamRead]
    search_fields = ["name"]
    ordering_fields = ["name", "kind", "value", "scope", "ends_on", "times_used", "usage_limit", "active"]
    filterset_fields = ["kind", "scope", "active"]
