from rest_framework.exceptions import PermissionDenied

from common.permissions import ADMIN, CUSTOMER, STAFF


def scope_to_user(queryset, user, path="customer"):
    """Team members see every record; a customer sees only their own."""
    if user.role == CUSTOMER:
        return queryset.filter(**{f"{path}__user": user} if path else {"user": user})
    return queryset


def ensure_can_manage(user, customer):
    """Staff may change only their assigned customers' records."""
    if user.role == ADMIN:
        return
    if user.role == STAFF and customer.assigned_to_id == user.id:
        return
    raise PermissionDenied("This customer isn't assigned to you.")
