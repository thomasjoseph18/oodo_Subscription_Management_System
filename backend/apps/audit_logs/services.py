from .models import AuditLog


def record(user, action, instance, before=None, after=None, **metadata):
    return AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        model=instance.__class__.__name__,
        object_id=str(instance.pk),
        before=before or {},
        after=after or {},
        metadata=metadata,
    )
