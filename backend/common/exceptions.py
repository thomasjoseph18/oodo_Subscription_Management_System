from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class BusinessRuleError(Exception):
    """A request that is well formed but breaks a business rule."""

    def __init__(self, message, code="business_rule"):
        super().__init__(message)
        self.message = message
        self.code = code


def api_exception_handler(exc, context):
    if isinstance(exc, BusinessRuleError):
        return Response(
            {"error": {"code": exc.code, "message": exc.message, "details": {}}},
            status=status.HTTP_409_CONFLICT,
        )
    response = exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    message = data.get("detail", "Please check the highlighted fields.") if isinstance(data, dict) else str(data)
    response.data = {
        "error": {
            "code": getattr(exc, "default_code", "error"),
            "message": str(message),
            "details": data if isinstance(data, dict) else {},
        }
    }
    return response
