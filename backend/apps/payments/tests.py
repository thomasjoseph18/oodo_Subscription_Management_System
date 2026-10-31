import hashlib
import hmac
import json
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.invoices import services as billing
from apps.invoices.models import Invoice
from apps.payments import services
from apps.payments.models import GatewayEvent, Payment
from apps.subscriptions import services as subs
from common import razorpay_client
from common.exceptions import BusinessRuleError
from conftest import client_for

TODAY = timezone.localdate


@pytest.fixture
def invoice(admin, customer, plan):
    subs.confirm(admin, subs.create_subscription(admin, customer, plan, TODAY()))
    billing.run_billing()
    return Invoice.objects.get()


@pytest.fixture
def gateway(settings, monkeypatch):
    settings.RAZORPAY_KEY_ID = "rzp_test_key"
    settings.RAZORPAY_KEY_SECRET = "secret"
    settings.RAZORPAY_WEBHOOK_SECRET = "hook"
    monkeypatch.setattr(razorpay_client, "create_order", lambda paise, receipt, notes: {"id": "order_1"})


def pay(user, invoice, amount, method="upi"):
    return services.record_payment(user, [(invoice.id, Decimal(amount))], method, TODAY())


def signed(body, secret="hook"):
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def webhook(event_id, event, entity, secret="hook"):
    body = json.dumps({"event": event, "payload": {"payment": {"entity": entity}}}).encode()
    return client_for().post(
        "/api/payments/razorpay/webhook/", data=body, content_type="application/json",
        headers={"X-Razorpay-Signature": signed(body, secret), "X-Razorpay-Event-Id": event_id},
    )


@pytest.mark.django_db
class TestManualPayments:
    def test_partial_then_full(self, staff, invoice):
        pay(staff, invoice, "400.00")
        invoice.refresh_from_db()
        assert (invoice.amount_paid, invoice.outstanding, invoice.status) == (Decimal("400.00"), Decimal("500.00"), "confirmed")
        assert invoice.payment_state(TODAY()) in ("partial", "overdue")
        pay(staff, invoice, "500.00")
        invoice.refresh_from_db()
        assert (invoice.outstanding, invoice.status) == (Decimal("0.00"), "paid")

    def test_overpayment_refused(self, staff, invoice):
        with pytest.raises(BusinessRuleError):
            pay(staff, invoice, "900.01")
        assert Payment.objects.count() == 0

    def test_one_payment_across_two_invoices(self, admin, staff, customer, plan):
        subs.confirm(admin, subs.create_subscription(admin, customer, plan, TODAY()))
        subs.confirm(admin, subs.create_subscription(admin, customer, plan, TODAY()))
        billing.run_billing()
        first, second = Invoice.objects.order_by("id")
        payment = services.record_payment(staff, [(first.id, Decimal("900")), (second.id, Decimal("100"))], "cash", TODAY())
        assert payment.amount == Decimal("1000.00")
        first.refresh_from_db(), second.refresh_from_db()
        assert first.status == "paid"
        assert second.outstanding == Decimal("800.00")

    def test_two_customers_cannot_share_a_payment(self, admin, staff, customer, other_customer, plan):
        subs.confirm(admin, subs.create_subscription(admin, customer, plan, TODAY()))
        subs.confirm(admin, subs.create_subscription(admin, other_customer, plan, TODAY()))
        billing.run_billing()
        first, second = Invoice.objects.order_by("id")
        with pytest.raises(BusinessRuleError):
            services.record_payment(staff, [(first.id, Decimal("1")), (second.id, Decimal("1"))], "cash", TODAY())

    def test_draft_cannot_be_paid(self, staff, invoice):
        Invoice.objects.update(status="draft")
        with pytest.raises(BusinessRuleError):
            pay(staff, invoice, "1.00")

    def test_invoice_with_payment_cannot_be_cancelled(self, admin, invoice):
        pay(admin, invoice, "1.00")
        with pytest.raises(BusinessRuleError):
            billing.cancel_invoice(admin, Invoice.objects.get())

    def test_api_records_note_and_shows_on_invoice(self, staff, invoice):
        client = client_for(staff)
        data = {"invoice": invoice.id, "amount": "100.00", "method": "cash", "paid_on": str(TODAY()), "notes": "At the desk"}
        response = client.post("/api/payments/", data, format="json")
        assert response.status_code == 201
        assert response.data["notes"] == "At the desk"
        assert client.get(f"/api/invoices/{invoice.id}/").data["payments"][0]["reference"].startswith("PAY-")

    def test_customers_cannot_record_or_see_others(self, customer, other_customer, staff, invoice):
        pay(staff, invoice, "1.00")
        data = {"invoice": invoice.id, "amount": "1.00", "method": "cash", "paid_on": str(TODAY())}
        assert client_for(customer.user).post("/api/payments/", data, format="json").status_code == 403
        assert client_for(customer.user).get("/api/payments/").data["count"] == 1
        assert client_for(other_customer.user).get("/api/payments/").data["count"] == 0

    def test_gateway_method_cannot_be_recorded_by_hand(self, staff, invoice):
        data = {"invoice": invoice.id, "amount": "1.00", "method": "online_gateway", "paid_on": str(TODAY())}
        assert client_for(staff).post("/api/payments/", data, format="json").status_code == 400


@pytest.mark.django_db
class TestRazorpay:
    def order(self, customer, invoice):
        return client_for(customer.user).post("/api/payments/razorpay/order/", {"invoice": invoice.id}, format="json")

    def test_order_for_own_invoice_only(self, gateway, customer, other_customer, invoice):
        assert client_for(other_customer.user).post("/api/payments/razorpay/order/", {"invoice": invoice.id}, format="json").status_code == 404
        response = self.order(customer, invoice)
        assert response.data["amount"] == 90000
        invoice.refresh_from_db()
        assert invoice.amount_paid == 0

    def test_disabled_without_keys(self, customer, invoice):
        assert self.order(customer, invoice).status_code == 409

    def test_webhook_settles_once_even_if_replayed(self, gateway, customer, invoice):
        self.order(customer, invoice)
        entity = {"id": "pay_1", "order_id": "order_1", "amount": 90000}
        assert webhook("evt_1", "payment.captured", entity).data["status"] == "applied"
        assert webhook("evt_1", "payment.captured", entity).data["status"] == "duplicate"
        assert webhook("evt_2", "payment.captured", entity).status_code == 200
        invoice.refresh_from_db()
        assert (invoice.status, invoice.amount_paid) == ("paid", Decimal("900.00"))
        assert GatewayEvent.objects.count() == 2

    def test_forged_webhook_rejected(self, gateway, customer, invoice):
        self.order(customer, invoice)
        response = webhook("evt_1", "payment.captured", {"id": "p", "order_id": "order_1", "amount": 90000}, secret="wrong")
        assert response.status_code == 401
        invoice.refresh_from_db()
        assert invoice.amount_paid == 0

    def test_wrong_amount_is_not_applied(self, gateway, customer, invoice):
        self.order(customer, invoice)
        with pytest.raises(BusinessRuleError):
            services.settle_gateway_payment("order_1", "pay_1", 100)

    def test_failed_payment_changes_nothing(self, gateway, customer, invoice):
        self.order(customer, invoice)
        webhook("evt_1", "payment.failed", {"id": "pay_1", "order_id": "order_1", "error_description": "Declined"})
        invoice.refresh_from_db()
        assert invoice.amount_paid == 0
        assert Payment.objects.get().status == "failed"

    def test_checkout_signature_checked(self, gateway, customer, invoice):
        self.order(customer, invoice)
        client = client_for(customer.user)
        bad = {"razorpay_order_id": "order_1", "razorpay_payment_id": "pay_1", "razorpay_signature": "nope"}
        assert client.post("/api/payments/razorpay/verify/", bad, format="json").status_code == 409
        good = {**bad, "razorpay_signature": signed(b"order_1|pay_1", "secret")}
        assert client.post("/api/payments/razorpay/verify/", good, format="json").status_code == 200
        invoice.refresh_from_db()
        assert invoice.status == "paid"
