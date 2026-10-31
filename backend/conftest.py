from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.customers.models import Customer
from apps.plans.models import PaymentTerm, Plan
from apps.products.models import Product, ProductVariant

User = get_user_model()


@pytest.fixture(autouse=True)
def no_throttling(settings):
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def client_for(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user)
    return client


@pytest.fixture
def admin(db):
    return User.objects.create_user("admin@test.io", "Passw0rd!x", role="admin")


@pytest.fixture
def staff(db):
    return User.objects.create_user("staff@test.io", "Passw0rd!x", role="staff")


@pytest.fixture
def customer(db, staff):
    user = User.objects.create_user("buyer@test.io", "Passw0rd!x")
    return Customer.objects.create(user=user, name="Buyer", email=user.email, assigned_to=staff)


@pytest.fixture
def other_customer(db):
    user = User.objects.create_user("other@test.io", "Passw0rd!x")
    return Customer.objects.create(user=user, name="Other", email=user.email)


@pytest.fixture
def product(db):
    return Product.objects.create(name="Loop CRM", product_type="software", sales_price=Decimal("1000.00"), cost_price=Decimal("300.00"))


@pytest.fixture
def variant(product):
    return ProductVariant.objects.create(product=product, name="Odoo", extra_price=Decimal("560.00"))


@pytest.fixture
def term(db):
    return PaymentTerm.objects.create(name="Net 15", days=15)


@pytest.fixture
def plan(product):
    return Plan.objects.create(
        name="Monthly", product=product, price=Decimal("900.00"), interval="monthly", min_quantity=1,
        available_from=timezone.localdate().replace(year=2020),
    )
