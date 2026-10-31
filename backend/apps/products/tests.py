from decimal import Decimal

import pytest

from apps.audit_logs.models import AuditLog
from apps.plans.services import line_unit_price
from conftest import client_for


@pytest.mark.django_db
class TestProducts:
    payload = {"name": "Sync", "product_type": "add_on", "sales_price": "100.00", "cost_price": "20.00"}

    def test_admin_creates_and_it_is_audited(self, admin):
        response = client_for(admin).post("/api/products/", self.payload, format="json")
        assert response.status_code == 201
        assert AuditLog.objects.filter(action="create", model="Product").exists()

    def test_staff_can_read_not_write(self, staff, product):
        client = client_for(staff)
        assert client.get("/api/products/").status_code == 200
        assert client.post("/api/products/", self.payload, format="json").status_code == 403

    def test_search_and_filter(self, admin, product):
        client = client_for(admin)
        assert client.get("/api/products/", {"search": "crm"}).data["count"] == 1
        assert client.get("/api/products/", {"status": "archived"}).data["count"] == 0

    def test_negative_price_rejected(self, admin):
        response = client_for(admin).post("/api/products/", {**self.payload, "sales_price": "-1"}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestVariantPricing:
    def test_odoo_variant_adds_560_to_sales_price(self, product, variant):
        assert line_unit_price(product, variant) == Decimal("1560.00")

    def test_variant_adds_to_plan_price(self, product, variant, plan):
        assert line_unit_price(product, variant, plan) == Decimal("1460.00")

    def test_changing_extra_changes_price(self, product, variant):
        variant.extra_price = Decimal("100.00")
        assert line_unit_price(product, variant) == Decimal("1100.00")

    def test_duplicate_variant_name_rejected(self, admin, product, variant):
        response = client_for(admin).post("/api/variants/", {"product": product.id, "name": "Odoo", "extra_price": "1"}, format="json")
        assert response.status_code == 400
