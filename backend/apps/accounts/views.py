from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from rest_framework import status, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from common.permissions import IsAdmin, STAFF
from common.viewsets import AuditedModelViewSet

from . import services
from .serializers import (
    ForgotPasswordSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    StaffSerializer,
    UserSerializer,
)

User = get_user_model()
COOKIE = "refresh_token"


def set_refresh_cookie(response, token):
    response.set_cookie(
        COOKIE,
        str(token),
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        path="/api/auth/",
    )


class PublicAuthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def get_authenticate_header(self, request):
        # Without this DRF reports failed logins as 403 instead of 401.
        return "Bearer"


class RegisterView(PublicAuthView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.register_customer(**serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(PublicAuthView):
    def post(self, request):
        user = authenticate(
            request,
            username=str(request.data.get("email", "")).lower(),
            password=request.data.get("password", ""),
        )
        if user is None:
            raise AuthenticationFailed("Incorrect email or password.")
        refresh = RefreshToken.for_user(user)
        response = Response({"access": str(refresh.access_token), "user": UserSerializer(user).data})
        set_refresh_cookie(response, refresh)
        return response


class RefreshView(PublicAuthView):
    throttle_scope = "anon"

    def post(self, request):
        token = request.COOKIES.get(COOKIE)
        if not token:
            raise AuthenticationFailed("Not signed in.")
        serializer = TokenRefreshSerializer(data={"refresh": token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as error:
            raise AuthenticationFailed("Session expired.") from error
        response = Response({"access": serializer.validated_data["access"]})
        set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


class LogoutView(PublicAuthView):
    def post(self, request):
        token = request.COOKIES.get(COOKIE)
        if token:
            try:
                RefreshToken(token).blacklist()
            except TokenError:
                pass
        response = Response({"status": "ok"})
        response.delete_cookie(COOKIE, path="/api/auth/")
        return response


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ForgotPasswordView(PublicAuthView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.send_password_reset(serializer.validated_data["email"])
        return Response({"status": "ok"})


class ResetPasswordView(PublicAuthView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reset_password(**serializer.validated_data)
        return Response({"status": "ok"})


class StaffViewSet(AuditedModelViewSet):
    """Only the admin can see or add members of staff."""

    serializer_class = StaffSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.filter(role=STAFF).order_by("email")
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["email", "first_name", "last_name"]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])
