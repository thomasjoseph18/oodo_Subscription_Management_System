from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.customers.models import Customer
from apps.notifications.services import notify
from common.exceptions import BusinessRuleError

User = get_user_model()


@transaction.atomic
def register_customer(name, email, password, company=""):
    first, _, last = name.partition(" ")
    user = User.objects.create_user(email, password, first_name=first, last_name=last)
    customer = Customer.objects.filter(email__iexact=email, user__isnull=True).first()
    if customer:
        customer.user = user
        customer.save(update_fields=["user", "updated_at"])
    else:
        Customer.objects.create(user=user, name=name, email=email, company=company)
    notify(user, "account_registered", "Welcome to Brightloop", "Your account is ready.")
    return user


def send_password_reset(email):
    """Silent when the email is unknown, so accounts can't be discovered."""
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if not user:
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
    notify(user, "password_reset", "Reset your Brightloop password", f"Use this link within an hour: {link}")


def reset_password(uid, token, password):
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None
    if user is None or not default_token_generator.check_token(user, token):
        raise BusinessRuleError("This reset link is invalid or has expired.", "invalid_reset_link")
    user.set_password(password)
    user.save(update_fields=["password"])
