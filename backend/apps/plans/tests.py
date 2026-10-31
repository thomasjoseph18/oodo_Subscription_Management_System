from datetime import date

import pytest

from common.billing_dates import first_period_on_or_after, period_end, period_start
from conftest import client_for


class TestBillingDates:
    def test_month_end_returns_to_31st(self):
        anchor = date(2026, 1, 31)
        assert [period_start(anchor, "monthly", n) for n in (1, 2)] == [date(2026, 2, 28), date(2026, 3, 31)]

    def test_leap_year_february(self):
        assert period_start(date(2024, 1, 31), "monthly", 1) == date(2024, 2, 29)

    def test_yearly_from_leap_day(self):
        anchor = date(2024, 2, 29)
        assert period_start(anchor, "yearly", 1) == date(2025, 2, 28)
        assert period_start(anchor, "yearly", 4) == date(2028, 2, 29)

    def test_daily_and_weekly(self):
        assert period_start(date(2026, 12, 31), "daily", 1) == date(2027, 1, 1)
        assert period_start(date(2026, 1, 1), "weekly", 2) == date(2026, 1, 15)

    def test_periods_touch_with_no_gap(self):
        anchor = date(2026, 1, 31)
        assert period_end(anchor, "monthly", 0) == date(2026, 2, 27)

    def test_first_period_after_a_pause(self):
        assert first_period_on_or_after(date(2026, 1, 10), "monthly", date(2026, 3, 11)) == 3


@pytest.mark.django_db
class TestPlans:
    def payload(self, product, **extra):
        return {"name": "Yearly", "product": product.id, "price": "9000", "interval": "yearly", "min_quantity": 1, "available_from": "2026-01-01", **extra}

    def test_admin_only_writes(self, admin, staff, product):
        assert client_for(admin).post("/api/plans/", self.payload(product), format="json").status_code == 201
        assert client_for(staff).post("/api/plans/", self.payload(product), format="json").status_code == 403

    def test_end_before_start_rejected(self, admin, product):
        response = client_for(admin).post("/api/plans/", self.payload(product, available_to="2025-01-01"), format="json")
        assert response.status_code == 400

    def test_customer_sees_only_available_plans(self, customer, plan):
        client = client_for(customer.user)
        assert client.get("/api/plans/").data["count"] == 1
        plan.status = "inactive"
        plan.save()
        assert client.get("/api/plans/").data["count"] == 0

    def test_is_available_respects_dates(self, plan):
        plan.available_to = date(2026, 6, 1)
        assert plan.is_available(date(2026, 6, 1))
        assert not plan.is_available(date(2026, 6, 2))
