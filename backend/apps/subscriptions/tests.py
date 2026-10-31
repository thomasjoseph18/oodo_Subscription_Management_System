from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.quotations import services as quotes
from apps.subscriptions import services
from apps.taxes.models import Tax
from common.exceptions import BusinessRuleError
from conftest import client_for


def make(user, customer, plan, start=None, **extra):
    return services.create_subscription(user, customer, plan, start or timezone.localdate(), **extra)


def active(user, customer, plan, start=None, **extra):
    subscription = make(user, customer, plan, start, **extra)
    return services.activate(user, services.confirm(user, subscription)) if (start or timezone.localdate()) > timezone.localdate() else services.confirm(user, subscription)


@pytest.mark.django_db
class TestLifecycle:
    def test_full_path_to_closed(self, admin, customer, plan):
        subscription = make(admin, customer, plan)
        assert subscription.status == "draft"
        subscription = services.quote(admin, subscription)
        assert subscription.status == "quotation"
        subscription = services.confirm(admin, subscription)
        assert subscription.status == "active"
        subscription = services.close(admin, subscription)
        assert subscription.status == "closed"
        assert subscription.events.count() == 5

    def test_future_start_stays_confirmed(self, admin, customer, plan):
        subscription = make(admin, customer, plan, timezone.localdate() + timedelta(days=5))
        assert services.confirm(admin, subscription).status == "confirmed"
        assert services.activate_due(timezone.localdate() + timedelta(days=5)) == 1

    @pytest.mark.parametrize("operation", [services.pause, services.resume, services.close, services.renew])
    def test_invalid_from_draft(self, admin, customer, plan, operation):
        with pytest.raises(BusinessRuleError):
            operation(admin, make(admin, customer, plan))

    def test_cannot_reopen_closed(self, admin, customer, plan):
        subscription = services.close(admin, active(admin, customer, plan))
        with pytest.raises(BusinessRuleError):
            services.resume(admin, subscription)

    def test_plan_flags_are_enforced(self, admin, customer, plan):
        plan.can_pause = plan.can_close_early = plan.can_renew = False
        plan.save()
        subscription = active(admin, customer, plan)
        assert services.allowed_actions(subscription) == []
        with pytest.raises(BusinessRuleError):
            services.pause(admin, subscription)

    def test_unavailable_plan_refused(self, admin, customer, plan):
        plan.status = "inactive"
        plan.save()
        with pytest.raises(BusinessRuleError):
            make(admin, customer, plan)

    def test_minimum_quantity_enforced(self, admin, customer, plan, product):
        plan.min_quantity = 5
        plan.save()
        with pytest.raises(BusinessRuleError):
            make(admin, customer, plan, lines=[{"product": product, "quantity": 2}])

    def test_resume_skips_paused_periods(self, admin, customer, plan):
        subscription = active(admin, customer, plan, )
        subscription = services.pause(admin, subscription)
        later = subscription.start_date + timedelta(days=75)
        subscription = services.resume(admin, subscription, today=later)
        assert subscription.next_billing_date >= later
        assert subscription.next_period >= 3

    def test_auto_close_only_when_plan_says_so(self, admin, customer, plan):
        subscription = active(admin, customer, plan, expiry_date=timezone.localdate() + timedelta(days=1))
        after = timezone.localdate() + timedelta(days=3)
        assert services.close_expired(after) == 0
        plan.auto_close = True
        plan.save()
        assert services.close_expired(after) == 1
        subscription.refresh_from_db()
        assert subscription.status == "closed"
        assert subscription.next_billing_date is None

    def test_renew_links_old_and_new(self, admin, customer, plan):
        old = active(admin, customer, plan)
        old.next_billing_date = date(2030, 1, 1)
        old.save()
        new = services.renew(admin, old)
        old.refresh_from_db()
        assert old.status == "renewed"
        assert new.status == "active" or new.status == "confirmed"
        assert new.renewed_from == old
        assert new.start_date == date(2030, 1, 1)
        with pytest.raises(BusinessRuleError):
            services.renew(admin, old)

    def test_approved_plan_change_reprices(self, admin, customer, plan, product):
        subscription = active(admin, customer, plan)
        plan.pk = None
        plan.name, plan.price = "Bigger", Decimal("2000.00")
        plan.save()
        change = services.request_plan_change(customer.user, subscription, plan)
        services.decide_plan_change(admin, change, True)
        subscription.refresh_from_db()
        assert subscription.plan == plan
        assert subscription.lines.get().unit_price == Decimal("2000.00")


@pytest.mark.django_db
class TestQuoteToSubscription:
    def test_template_quote_converts_on_same_terms(self, admin, customer, plan, term, product, variant):
        from apps.quotations.models import QuotationTemplate, QuotationTemplateLine

        template = QuotationTemplate.objects.create(name="Std", plan=plan, payment_term=term, validity_days=10)
        QuotationTemplateLine.objects.create(template=template, product=product, variant=variant, quantity=3)
        Tax.objects.create(name="GST", rate=Decimal("18.00"))
        quotation = quotes.create_quotation(admin, customer, template=template)
        assert quotation.valid_until == timezone.localdate() + timedelta(days=10)
        assert quotation.subtotal == Decimal("4380.00")
        assert quotation.total == Decimal("5168.40")
        with pytest.raises(BusinessRuleError):
            services.create_from_quotation(admin, quotation)
        quotes.accept(admin, quotes.send(admin, quotation))
        subscription = services.create_from_quotation(admin, quotation)
        assert subscription.status == "active"
        assert subscription.payment_term == term
        assert subscription.total == quotation.total
        assert subscription.lines.get().unit_price == Decimal("1460.00")
        with pytest.raises(BusinessRuleError):
            services.create_from_quotation(admin, quotation)

    def test_expired_quote_cannot_be_accepted(self, admin, customer, plan):
        quotation = quotes.send(admin, quotes.create_quotation(admin, customer, plan=plan))
        assert quotes.expire_overdue(quotation.valid_until + timedelta(days=1)) == 1
        quotation.refresh_from_db()
        with pytest.raises(BusinessRuleError):
            quotes.accept(admin, quotation)

    def test_pdf_downloads(self, admin, customer, plan):
        quotation = quotes.create_quotation(admin, customer, plan=plan)
        response = client_for(admin).get(f"/api/quotations/{quotation.id}/pdf/")
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF")


@pytest.mark.django_db
class TestAccess:
    def test_customers_see_only_their_own(self, admin, customer, other_customer, plan):
        subscription = make(admin, customer, plan)
        client = client_for(other_customer.user)
        assert client.get("/api/subscriptions/").data["count"] == 0
        assert client.get(f"/api/subscriptions/{subscription.id}/").status_code == 404
        assert client.post(f"/api/subscriptions/{subscription.id}/pause/").status_code == 404

    def test_customer_can_pause_own(self, admin, customer, plan):
        subscription = active(admin, customer, plan)
        assert client_for(customer.user).post(f"/api/subscriptions/{subscription.id}/pause/").status_code == 200

    def test_customer_cannot_confirm_or_create(self, admin, customer, plan):
        subscription = make(admin, customer, plan)
        client = client_for(customer.user)
        assert client.post(f"/api/subscriptions/{subscription.id}/confirm/").status_code == 403
        assert client.post("/api/subscriptions/", {}, format="json").status_code == 403

    def test_staff_views_all_but_changes_assigned_only(self, admin, staff, customer, other_customer, plan):
        mine, theirs = make(admin, customer, plan), make(admin, other_customer, plan)
        client = client_for(staff)
        assert client.get("/api/subscriptions/").data["count"] == 2
        assert client.post(f"/api/subscriptions/{mine.id}/confirm/").status_code == 200
        assert client.post(f"/api/subscriptions/{theirs.id}/confirm/").status_code == 403

    def test_invalid_transition_returns_409(self, admin, customer, plan):
        subscription = make(admin, customer, plan)
        response = client_for(admin).post(f"/api/subscriptions/{subscription.id}/close/")
        assert response.status_code == 409
        assert response.data["error"]["code"] == "invalid_transition"
