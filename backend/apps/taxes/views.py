from rest_framework import serializers

from common.permissions import AdminWriteTeamRead
from common.viewsets import AuditedModelViewSet

from .models import Tax


class TaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax
        fields = ["id", "name", "kind", "rate", "description", "active", "applies_to_all", "products"]


class TaxViewSet(AuditedModelViewSet):
    queryset = Tax.objects.prefetch_related("products")
    serializer_class = TaxSerializer
    permission_classes = [AdminWriteTeamRead]
    search_fields = ["name"]
    ordering_fields = ["name", "kind", "rate", "active"]
    filterset_fields = ["active", "kind"]
