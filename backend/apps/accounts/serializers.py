from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.permissions import ADMIN, STAFF

from .validators import validate_password_rule

User = get_user_model()


def validate_unique_email(value):
    email = value.lower()
    if User.objects.filter(email__iexact=email).exists():
        raise serializers.ValidationError("An account with this email already exists.")
    return email


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role"]
        read_only_fields = ["id", "email", "role"]


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    company = serializers.CharField(max_length=200, required=False, allow_blank=True)
    email = serializers.EmailField(validators=[validate_unique_email])
    password = serializers.CharField(validators=[validate_password_rule], write_only=True)


class StaffSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password_rule])

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "password"]
        read_only_fields = ["id", "role"]

    def validate_email(self, value):
        if self.instance and self.instance.email == value.lower():
            return value.lower()
        return validate_unique_email(value)

    def create(self, validated_data):
        return User.objects.create_user(role=STAFF, is_staff=True, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(validators=[validate_password_rule])


TEAM_ROLES = (ADMIN, STAFF)
