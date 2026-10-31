from rest_framework import serializers, viewsets

from common.permissions import IsAdmin

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", default=None, read_only=True)

    class Meta:
        model = AuditLog
        fields = ["id", "user_email", "action", "model", "object_id", "before", "after", "metadata", "created_at"]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related("user")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["action", "model"]
    search_fields = ["object_id", "user__email", "action"]
