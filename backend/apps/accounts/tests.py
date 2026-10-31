import re

import pytest
from django.core import mail

from apps.customers.models import Customer
from conftest import client_for

REGISTER = "/api/auth/register/"
GOOD = {"name": "Asha Rao", "company": "Shop", "email": "asha@shop.io", "password": "Str0ng!pass"}


@pytest.mark.django_db
class TestRegistration:
    def test_creates_customer_account(self):
        assert client_for().post(REGISTER, GOOD, format="json").status_code == 201
        customer = Customer.objects.get(email="asha@shop.io")
        assert customer.user.role == "customer"

    def test_email_is_unique_ignoring_case(self):
        client_for().post(REGISTER, GOOD, format="json")
        response = client_for().post(REGISTER, {**GOOD, "email": "ASHA@shop.io"}, format="json")
        assert response.status_code == 400

    @pytest.mark.parametrize("password", ["Abcdef1!", "abcdefgh1!", "ABCDEFGH1!", "Abcdefghi1"])
    def test_rejects_weak_passwords(self, password):
        response = client_for().post(REGISTER, {**GOOD, "password": password}, format="json")
        assert response.status_code == 400
        assert "password" in response.data["error"]["details"]

    def test_role_cannot_be_chosen(self):
        client_for().post(REGISTER, {**GOOD, "role": "admin"}, format="json")
        assert Customer.objects.get(email="asha@shop.io").user.role == "customer"


@pytest.mark.django_db
class TestLogin:
    def test_login_sets_httponly_refresh_cookie(self, customer):
        client = client_for()
        response = client.post("/api/auth/login/", {"email": customer.email, "password": "Passw0rd!x"}, format="json")
        assert response.status_code == 200
        assert response.data["user"]["role"] == "customer"
        assert response.cookies["refresh_token"]["httponly"]
        assert client.post("/api/auth/refresh/").status_code == 200

    def test_wrong_password(self, customer):
        response = client_for().post("/api/auth/login/", {"email": customer.email, "password": "nope"}, format="json")
        assert response.status_code == 401

    def test_refresh_fails_after_logout(self, customer):
        client = client_for()
        client.post("/api/auth/login/", {"email": customer.email, "password": "Passw0rd!x"}, format="json")
        old = client.cookies["refresh_token"].value
        client.post("/api/auth/logout/")
        client.cookies["refresh_token"] = old
        assert client.post("/api/auth/refresh/").status_code == 401


@pytest.mark.django_db
class TestPasswordReset:
    def test_reset_link_arrives_and_works(self, customer, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            client_for().post("/api/auth/password/forgot/", {"email": customer.email}, format="json")
        uid, token = re.search(r"reset-password/([^/]+)/(\S+)", mail.outbox[0].body).groups()
        new = {"uid": uid, "token": token, "password": "N3w!passwd"}
        assert client_for().post("/api/auth/password/reset/", new, format="json").status_code == 200
        assert client_for().post("/api/auth/login/", {"email": customer.email, "password": "N3w!passwd"}, format="json").status_code == 200
        assert client_for().post("/api/auth/password/reset/", new, format="json").status_code == 409

    def test_unknown_email_looks_the_same(self):
        response = client_for().post("/api/auth/password/forgot/", {"email": "ghost@x.io"}, format="json")
        assert response.status_code == 200
        assert mail.outbox == []


@pytest.mark.django_db
class TestStaffAccounts:
    payload = {"email": "new@brightloop.io", "password": "Str0ng!pass"}

    def test_admin_adds_staff(self, admin):
        response = client_for(admin).post("/api/users/", self.payload, format="json")
        assert response.status_code == 201
        assert response.data["role"] == "staff"

    def test_staff_and_customers_cannot(self, staff, customer):
        assert client_for(staff).post("/api/users/", self.payload, format="json").status_code == 403
        assert client_for(customer.user).post("/api/users/", self.payload, format="json").status_code == 403
