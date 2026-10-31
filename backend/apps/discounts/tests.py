from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.discounts import services
from apps.discounts.models import Discount
from apps.invoices import services as billing
from apps.invoices.models import Invoice
from apps.subscriptions import services as subs
from apps.taxes.models import Tax
from conftest import client_for


def discount(**extra):
    defaults = {"name": "Ten", "kind": "percent", "value": Decimal("10"), "starts_on": date(2020, 1, 1)}
    return Discount.objects.create(**{**defaults, **extra})


@pytest.fixture
def subscription(admin, customer, plan):
    return subs.confirm(admin, subs.create_subscription(admin, customer, plan, timezone.localdate() - timedelta(days=65)))


@pytest.mark.django_db
class TestDiscounts:
    def test_only_admin_creates(self, admin, staff):
        payload = {"name": "A", "kind": "fixed", "value": "50", "scope": "subscription", "starts_on": "2026-01-01"}
        assert client_for(staff).post("/api/discounts/", payload, format="json").status_code == 403
        assert client_for(admin).post("/api/discounts/", payload, format="json").status_code == 201

    def test_percent_over_100_rejected(self, admin):
        payload = {"name": "A", "kind": "percent", "value": "101", "scope": "subscription", "starts_on": "2026-01-01"}
        assert client_for(admin).post("/api/discounts/", payload, format="json").status_code == 400

    def test_appears_on_next_invoice_before_tax(self, subscription):
        Tax.objects.create(name="GST", rate=Decimal("18"))
        discount()
        billing.run_billing()
        invoice = Invoice.objects.order_by("id").first()
        assert invoice.discount_total == Decimal("90.00")
        assert invoice.tax_total == Decimal("145.80")
        assert invoice.total == Decimal("955.80")

    def test_usage_limit_stops_it(self, subscription):
        rule = discount(usage_limit=2)
        billing.run_billing()
        totals = list(Invoice.objects.order_by("period_start").values_list("discount_total", flat=True))
        assert totals == [Decimal("90.00"), Decimal("90.00"), Decimal("0.00")]
        rule.refresh_from_db()
        assert rule.times_used == 2

    def test_expired_is_ignored(self, subscription):
        discount(ends_on=timezone.localdate() - timedelta(days=1))
        billing.run_billing()
        assert all(invoice.discount_total == 0 for invoice in Invoice.objects.all())

    def test_future_is_ignored(self, subscription):
        discount(starts_on=timezone.localdate() + timedelta(days=1))
        billing.run_billing()
        assert all(invoice.discount_total == 0 for invoice in Invoice.objects.all())

    def test_minimum_quantity_and_purchase(self, subscription):
        discount(min_quantity=5)
        discount(name="Big", min_purchase=Decimal("5000"))
        billing.run_billing()
        assert all(invoice.discount_total == 0 for invoice in Invoice.objects.all())

    def test_product_scope(self, subscription, product):
        other = discount(scope="product")
        billing.run_billing()
        assert all(invoice.discount_total == 0 for invoice in Invoice.objects.all())
        other.products.add(product)

    def test_best_one_wins_no_stacking(self, subscription):
        discount()
        discount(name="Twenty", value=Decimal("20"))
        billing.run_billing()
        assert Invoice.objects.order_by("id").first().discount_total == Decimal("180.00")

    def test_fixed_never_exceeds_price(self, subscription):
        discount(kind="fixed", value=Decimal("5000"))
        billing.run_billing()
        assert Invoice.objects.order_by("id").first().total == Decimal("0.00")

    def test_cancelling_gives_the_use_back(self, admin, subscription):
        rule = discount(usage_limit=5)
        billing.run_billing()
        used = Discount.objects.get(pk=rule.pk).times_used
        billing.cancel_invoice(admin, Invoice.objects.order_by("id").first())
        assert Discount.objects.get(pk=rule.pk).times_used == used - 1

    def test_preview_uses_nothing(self, subscription):
        rule = discount(usage_limit=1)
        services.preview(list(subscription.lines.all()), timezone.localdate())
        rule.refresh_from_db()
        assert rule.times_used == 0
