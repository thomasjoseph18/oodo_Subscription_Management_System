from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.invoices import services
from apps.invoices.models import BillingSettings, Invoice
from apps.subscriptions import services as subs
from apps.taxes.models import Tax
from common.exceptions import BusinessRuleError
from conftest import client_for


@pytest.fixture
def gst(db):
    return Tax.objects.create(name="GST", rate=Decimal("18.00"))


@pytest.fixture
def subscription(admin, customer, plan, term, gst):
    start = timezone.localdate()
    return subs.confirm(admin, subs.create_subscription(admin, customer, plan, start, payment_term=term))


@pytest.mark.django_db
class TestBilling:
    def test_invoice_is_filled_from_subscription(self, subscription, term, customer):
        run = services.run_billing()
        assert run.invoices_created == 1
        invoice = Invoice.objects.get()
        assert invoice.customer == customer
        assert invoice.number.startswith("INV-")
        assert invoice.status == "confirmed"
        assert invoice.subtotal == Decimal("900.00")
        assert invoice.tax_total == Decimal("162.00")
        assert invoice.total == Decimal("1062.00")
        assert invoice.due_date == invoice.invoice_date + timedelta(days=term.days)
        assert invoice.lines.get().taxes.get().name == "GST"

    def test_running_twice_bills_once(self, subscription):
        services.run_billing()
        assert services.run_billing().invoices_created == 0
        assert Invoice.objects.count() == 1

    def test_database_refuses_a_second_invoice_for_a_period(self, subscription):
        services.run_billing()
        invoice = Invoice.objects.get()
        with pytest.raises(IntegrityError), transaction.atomic():
            Invoice.objects.create(
                customer=invoice.customer, subscription=invoice.subscription, invoice_date=invoice.invoice_date,
                due_date=invoice.due_date, period_start=invoice.period_start, period_end=invoice.period_end,
            )

    def test_missed_days_catch_up_with_no_gaps(self, admin, customer, plan, gst):
        start = date(2026, 1, 31)
        subscription = subs.create_subscription(admin, customer, plan, start)
        subs.confirm(admin, subscription)
        run = services.run_billing(date(2026, 4, 1))
        assert run.invoices_created == 3
        periods = list(Invoice.objects.order_by("period_start").values_list("period_start", "period_end"))
        assert periods == [
            (date(2026, 1, 31), date(2026, 2, 27)),
            (date(2026, 2, 28), date(2026, 3, 30)),
            (date(2026, 3, 31), date(2026, 4, 29)),
        ]

    def test_paused_and_closed_are_not_billed(self, admin, subscription):
        subs.pause(admin, subscription)
        assert services.run_billing().invoices_created == 0

    def test_stops_at_expiry(self, admin, customer, plan, gst):
        subscription = subs.create_subscription(admin, customer, plan, date(2026, 1, 1), expiry_date=date(2026, 2, 15))
        subs.confirm(admin, subscription)
        assert services.run_billing(date(2026, 6, 1)).invoices_created == 2

    def test_later_tax_change_keeps_old_invoices(self, subscription, gst):
        services.run_billing()
        gst.rate = Decimal("28.00")
        gst.save()
        assert Invoice.objects.get().tax_total == Decimal("162.00")

    def test_tax_only_on_listed_product(self, admin, customer, plan, gst, product):
        gst.applies_to_all = False
        gst.save()
        subs.confirm(admin, subs.create_subscription(admin, customer, plan, timezone.localdate()))
        services.run_billing()
        assert Invoice.objects.get().tax_total == Decimal("0.00")
        gst.products.add(product)

    def test_auto_confirm_can_be_turned_off(self, subscription):
        BillingSettings.objects.update_or_create(pk=1, defaults={"auto_confirm_invoices": False})
        services.run_billing()
        assert Invoice.objects.get().status == "draft"

    def test_one_failure_does_not_stop_the_run(self, admin, subscription, monkeypatch):
        original = services._build_invoice
        calls = []

        def flaky(*args):
            calls.append(1)
            if len(calls) == 1:
                raise ValueError("boom")
            return original(*args)

        monkeypatch.setattr(services, "_build_invoice", flaky)
        run = services.run_billing()
        assert run.failures and run.invoices_created == 0
        subscription.refresh_from_db()
        assert subscription.next_period == 0
        monkeypatch.undo()
        assert services.run_billing().invoices_created == 1


@pytest.mark.django_db
class TestInvoiceActions:
    def test_cancel_then_reissue_same_period(self, admin, subscription):
        services.run_billing()
        invoice = Invoice.objects.get()
        services.cancel_invoice(admin, invoice)
        invoice.refresh_from_db()
        new = services.reissue_invoice(admin, invoice)
        assert new.period_start == invoice.period_start
        assert new.status == "draft"
        with pytest.raises(BusinessRuleError):
            services.reissue_invoice(admin, invoice)

    def test_paid_invoice_cannot_be_cancelled(self, admin, subscription):
        services.run_billing()
        Invoice.objects.update(status="paid", amount_paid=Decimal("1062.00"))
        with pytest.raises(BusinessRuleError):
            services.cancel_invoice(admin, Invoice.objects.get())

    def test_pdf_and_send(self, admin, staff, subscription, mailoutbox):
        services.run_billing()
        invoice = Invoice.objects.get()
        assert client_for(staff).get(f"/api/invoices/{invoice.id}/pdf/").content.startswith(b"%PDF")
        assert client_for(staff).post(f"/api/invoices/{invoice.id}/send/").status_code == 200
        assert mailoutbox[0].attachments[0][2] == "application/pdf"

    def test_customer_isolation_and_no_actions(self, customer, other_customer, subscription):
        services.run_billing()
        invoice = Invoice.objects.get()
        assert client_for(customer.user).get(f"/api/invoices/{invoice.id}/").status_code == 200
        assert client_for(other_customer.user).get(f"/api/invoices/{invoice.id}/").status_code == 404
        assert client_for(customer.user).post(f"/api/invoices/{invoice.id}/cancel/").status_code == 403

    def test_payment_state_filter(self, admin, subscription):
        services.run_billing()
        Invoice.objects.update(due_date=timezone.localdate() - timedelta(days=1))
        client = client_for(admin)
        assert client.get("/api/invoices/", {"payment_state": "overdue"}).data["count"] == 1
        assert client.get("/api/invoices/", {"payment_state": "paid"}).data["count"] == 0

    def test_billing_run_button_is_team_only(self, staff, customer, subscription):
        assert client_for(customer.user).post("/api/billing-runs/").status_code == 403
        assert client_for(staff).post("/api/billing-runs/").data["invoices_created"] == 1
