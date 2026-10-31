from django.utils import timezone
from rest_framework import permissions, serializers

from common.permissions import CUSTOMER, AdminWriteTeamRead, IsAdmin
from common.viewsets import AuditedModelViewSet

from .models import PaymentTerm, Plan


class PaymentTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = ["id", "name", "days"]


class PlanSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id", "name", "product", "product_name", "price", "interval", "min_quantity", "available_from", "available_to",
            "auto_close", "can_close_early", "can_pause", "can_renew", "status",
        ]

    def validate(self, attrs):
        start = attrs.get("available_from") or getattr(self.instance, "available_from", None)
        end = attrs.get("available_to", getattr(self.instance, "available_to", None))
        if end and start and end < start:
            raise serializers.ValidationError({"available_to": ["This can't be before the start date."]})
        return attrs


class PaymentTermViewSet(AuditedModelViewSet):
    queryset = PaymentTerm.objects.all()
    serializer_class = PaymentTermSerializer
    permission_classes = [AdminWriteTeamRead]
    ordering_fields = ["name", "days"]


class PlanViewSet(AuditedModelViewSet):
    queryset = Plan.objects.select_related("product")
    serializer_class = PlanSerializer
    search_fields = ["name", "product__name"]
    ordering_fields = ["name", "price", "interval", "min_quantity", "status"]
    filterset_fields = ["interval", "status", "product"]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != CUSTOMER:
            return queryset
        today = timezone.localdate()
        available = queryset.filter(status="active", available_from__lte=today)
        return available.filter(available_to__isnull=True) | available.filter(available_to__gte=today)
