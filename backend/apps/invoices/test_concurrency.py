"""Needs real row locks, so it runs only on PostgreSQL."""
import threading
from decimal import Decimal

import pytest
from django.db import connection, connections
from django.utils import timezone

from apps.invoices import services as billing
from apps.invoices.models import Invoice
from apps.payments import services as payments
from apps.subscriptions import services as subs

pytestmark = pytest.mark.skipif(connection.vendor != "postgresql", reason="needs PostgreSQL row locks")


def in_threads(count, target):
    errors = []

    def wrapped():
        try:
            target()
        except Exception as error:
            errors.append(error)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=wrapped) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return errors


@pytest.mark.django_db(transaction=True)
def test_parallel_billing_runs_never_double_bill(admin, customer, plan):
    for _ in range(10):
        subs.confirm(admin, subs.create_subscription(admin, customer, plan, timezone.localdate()))
    assert in_threads(4, billing.run_billing) == []
    assert Invoice.objects.count() == 10


@pytest.mark.django_db(transaction=True)
def test_parallel_payments_never_overpay(admin, customer, plan):
    subs.confirm(admin, subs.create_subscription(admin, customer, plan, timezone.localdate()))
    billing.run_billing()
    invoice = Invoice.objects.get()
    errors = in_threads(4, lambda: payments.record_payment(admin, [(invoice.id, Decimal("500.00"))], "cash", timezone.localdate()))
    invoice.refresh_from_db()
    assert invoice.amount_paid == Decimal("500.00")
    assert len(errors) == 3
