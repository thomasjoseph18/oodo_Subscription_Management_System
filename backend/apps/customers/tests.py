import pytest

from apps.customers.models import Customer
from conftest import client_for


@pytest.mark.django_db
class TestCustomerAccess:
    def test_customer_cannot_list_customers(self, customer):
        assert client_for(customer.user).get("/api/customers/").status_code == 403

    def test_customer_updates_own_billing_only(self, customer):
        client = client_for(customer.user)
        response = client.patch("/api/customers/me/", {"billing_address": "1 MG Road", "email": "x@y.io"}, format="json")
        assert response.status_code == 200
        customer.refresh_from_db()
        assert customer.billing_address == "1 MG Road"
        assert customer.email == "buyer@test.io"

    def test_staff_edits_assigned_but_not_others(self, staff, customer, other_customer):
        client = client_for(staff)
        assert client.patch(f"/api/customers/{customer.id}/", {"phone": "1"}, format="json").status_code == 200
        assert client.patch(f"/api/customers/{other_customer.id}/", {"phone": "1"}, format="json").status_code == 403

    def test_staff_can_view_all(self, staff, customer, other_customer):
        assert client_for(staff).get("/api/customers/").data["count"] == 2

    def test_new_customer_is_assigned_to_creating_staff(self, staff):
        client_for(staff).post("/api/customers/", {"name": "New", "email": "n@x.io"}, format="json")
        assert Customer.objects.get(email="n@x.io").assigned_to == staff

    def test_delete_is_soft(self, admin, customer):
        client_for(admin).delete(f"/api/customers/{customer.id}/")
        assert not Customer.objects.filter(pk=customer.pk).exists()
        assert Customer.all_objects.filter(pk=customer.pk).exists()
