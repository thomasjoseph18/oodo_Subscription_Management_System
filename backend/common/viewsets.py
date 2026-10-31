from django.forms.models import model_to_dict
from rest_framework import viewsets

from apps.audit_logs.services import record


def _snapshot(instance):
    return {key: str(value) for key, value in model_to_dict(instance).items() if not isinstance(value, list)}


class AuditedModelViewSet(viewsets.ModelViewSet):
    """CRUD with an audit trail. Soft-deletable models are hidden, not removed."""

    def perform_create(self, serializer):
        instance = serializer.save()
        record(self.request.user, "create", instance, after=_snapshot(instance))

    def perform_update(self, serializer):
        before = _snapshot(serializer.instance)
        instance = serializer.save()
        record(self.request.user, "update", instance, before=before, after=_snapshot(instance))

    def perform_destroy(self, instance):
        record(self.request.user, "delete", instance, before=_snapshot(instance))
        if hasattr(instance, "soft_delete"):
            instance.soft_delete()
        else:
            instance.delete()
