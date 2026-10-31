from rest_framework.permissions import SAFE_METHODS, BasePermission

ADMIN = "admin"
STAFF = "staff"
CUSTOMER = "customer"


def _role(request):
    return getattr(request.user, "role", None) if request.user.is_authenticated else None


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return _role(request) == ADMIN


class IsTeam(BasePermission):
    """Admin or internal staff."""

    def has_permission(self, request, view):
        return _role(request) in (ADMIN, STAFF)


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return _role(request) == CUSTOMER


class AdminWriteTeamRead(BasePermission):
    """Configuration data: the team reads it, only the admin changes it."""

    def has_permission(self, request, view):
        role = _role(request)
        return role == ADMIN or (role == STAFF and request.method in SAFE_METHODS)
