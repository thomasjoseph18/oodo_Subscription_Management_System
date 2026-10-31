from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.audit_logs.services import record
from apps.discounts import services as discounts
from apps.notifications.services import notify
from apps.plans.services import ensure_available, line_unit_price
from apps.quotations.services import build_lines
from apps.taxes.services import price_lines
from common.billing_dates import first_period_on_or_after, period_start
from common.exceptions import BusinessRuleError

from .models import PlanChangeRequest, Subscription, SubscriptionEvent, SubscriptionLine

TRANSITIONS = {
    "quote": ({"draft"}, "quotation"),
    "confirm": ({"draft", "quotation"}, "confirmed"),
    "activate": ({"confirmed"}, "active"),
    "pause": ({"active"}, "paused"),
    "resume": ({"paused"}, "active"),
    "renew": ({"active"}, "renewed"),
    "close": ({"active"}, "closed"),
}
PLAN_RULES = {"pause": "can_pause", "renew": "can_renew", "close": "can_close_early"}


def allowed_actions(subscription):
    return [
        name for name, (sources, _) in TRANSITIONS.items()
        if subscription.status in sources and getattr(subscription.plan, PLAN_RULES.get(name, ""), True)
    ]


def _transition(user, subscription, action, message):
    if action not in allowed_actions(subscription):
        raise BusinessRuleError(f"A {subscription.status} subscription can't {action} under {subscription.plan.name}.", "invalid_transition")
    old, new = subscription.status, TRANSITIONS[action][1]
    subscription.status = new
    subscription.save()
    SubscriptionEvent.objects.create(subscription=subscription, actor=user, from_status=old, to_status=new, message=message)
    record(user, action, subscription, before={"status": old}, after={"status": new})


def _locked(subscription):
    return Subscription.objects.select_for_update(of=("self",)).select_related("plan", "customer__user").get(pk=subscription.pk)


def _create(user, customer, plan, start_date, expiry_date, payment_term, lines, status="draft", **extra):
    subscription = Subscription.objects.create(
        customer=customer, plan=plan, start_date=start_date, expiry_date=expiry_date, payment_term=payment_term, status=status, **extra,
    )
    price_lines(subscription, lines, discounts.preview(lines, timezone.localdate()))
    for line in lines:
        line.subscription = subscription
    SubscriptionLine.objects.bulk_create(lines)
    subscription.number = f"SUB-{subscription.pk:06d}"
    subscription.save()
    SubscriptionEvent.objects.create(subscription=subscription, actor=user, to_status=status, message="Subscription created")
    record(user, "create", subscription)
    return subscription


@transaction.atomic
def create_subscription(user, customer, plan, start_date, expiry_date=None, payment_term=None, lines=None):
    if expiry_date and expiry_date < start_date:
        raise BusinessRuleError("The expiry date can't be before the start date.", "invalid_dates")
    ensure_available(plan, start_date)
    built = build_lines(plan, lines, SubscriptionLine)
    return _create(user, customer, plan, start_date, expiry_date, payment_term, built)


@transaction.atomic
def create_from_quotation(user, quotation):
    """An accepted quotation becomes a confirmed subscription on the same
    terms: lines keep the quoted prices."""
    if quotation.status != "accepted":
        raise BusinessRuleError("Only an accepted quotation can become a subscription.", "invalid_transition")
    if Subscription.objects.filter(source_quotation=quotation).exists():
        raise BusinessRuleError("This quotation already has a subscription.", "already_converted")
    lines = [
        SubscriptionLine(product=line.product, variant=line.variant, description=line.description, quantity=line.quantity, unit_price=line.unit_price)
        for line in quotation.lines.all()
    ]
    today = timezone.localdate()
    subscription = _create(
        user, quotation.customer, quotation.plan, today, None, quotation.payment_term, lines, status="confirmed", source_quotation=quotation,
    )
    return activate_if_due(user, subscription, today)


def _start_billing(subscription):
    subscription.next_period = 0
    subscription.next_billing_date = subscription.start_date


@transaction.atomic
def quote(user, subscription):
    subscription = _locked(subscription)
    _transition(user, subscription, "quote", "Marked as quotation")
    return subscription


@transaction.atomic
def confirm(user, subscription):
    subscription = _locked(subscription)
    _transition(user, subscription, "confirm", "Confirmed")
    return activate_if_due(user, subscription, timezone.localdate())


def activate_if_due(user, subscription, today):
    if subscription.start_date <= today:
        return activate(user, subscription)
    return subscription


@transaction.atomic
def activate(user, subscription):
    subscription = _locked(subscription)
    _start_billing(subscription)
    _transition(user, subscription, "activate", "Activated")
    notify(subscription.customer.user, "subscription_activated", f"Subscription {subscription.number} is active")
    return subscription


@transaction.atomic
def pause(user, subscription):
    subscription = _locked(subscription)
    _transition(user, subscription, "pause", "Paused")
    return subscription


@transaction.atomic
def resume(user, subscription, today=None):
    """Periods that passed during the pause aren't billed. Billing picks up
    at the next regular date."""
    subscription = _locked(subscription)
    today = today or timezone.localdate()
    resume_from = max(today, subscription.next_billing_date or today)
    n = first_period_on_or_after(subscription.start_date, subscription.plan.interval, resume_from)
    subscription.next_period = n
    subscription.next_billing_date = period_start(subscription.start_date, subscription.plan.interval, n)
    _transition(user, subscription, "resume", "Resumed")
    return subscription


@transaction.atomic
def close(user, subscription, message="Closed early"):
    subscription = _locked(subscription)
    subscription.next_billing_date = None
    subscription.closed_at = timezone.now()
    _transition(user, subscription, "close", message)
    return subscription


@transaction.atomic
def renew(user, subscription):
    """The current term ends as Renewed and a linked subscription continues
    from the next billing date, so no period is skipped or repeated."""
    subscription = _locked(subscription)
    start = subscription.next_billing_date or timezone.localdate()
    subscription.next_billing_date = None
    _transition(user, subscription, "renew", "Renewed")
    ensure_available(subscription.plan, timezone.localdate())
    expiry = None
    if subscription.expiry_date:
        expiry = start + (subscription.expiry_date - subscription.start_date)
    lines = [
        SubscriptionLine(product=line.product, variant=line.variant, description=line.description, quantity=line.quantity, unit_price=line.unit_price)
        for line in subscription.lines.all()
    ]
    new = _create(
        user, subscription.customer, subscription.plan, start, expiry, subscription.payment_term, lines, status="confirmed", renewed_from=subscription,
    )
    return activate(user, new)


@transaction.atomic
def request_plan_change(user, subscription, plan):
    if subscription.status != "active":
        raise BusinessRuleError("Only an active subscription can change plan.", "invalid_transition")
    ensure_available(plan, timezone.localdate())
    if subscription.plan_changes.filter(status="pending").exists():
        raise BusinessRuleError("A plan change is already waiting for approval.", "already_requested")
    change = PlanChangeRequest.objects.create(subscription=subscription, plan=plan, requested_by=user)
    SubscriptionEvent.objects.create(subscription=subscription, actor=user, message=f"Asked to change to {plan.name}")
    return change


@transaction.atomic
def decide_plan_change(user, change, approve):
    """An approved change reprices the plan's line from the next invoice.
    Plans with another billing interval need a new subscription."""
    subscription = _locked(change.subscription)
    if change.status != "pending":
        raise BusinessRuleError("This request has already been decided.", "already_decided")
    if approve and change.plan.interval != subscription.plan.interval:
        raise BusinessRuleError("The new plan must bill at the same interval.", "interval_mismatch")
    change.status = "approved" if approve else "rejected"
    change.save(update_fields=["status"])
    if approve:
        old_plan = subscription.plan
        lines = list(subscription.lines.all())
        for line in lines:
            if line.product_id == old_plan.product_id:
                line.product = change.plan.product
                line.description = change.plan.product.name
                line.variant = None
                line.unit_price = line_unit_price(change.plan.product, None, change.plan)
        subscription.plan = change.plan
        price_lines(subscription, lines)
        SubscriptionLine.objects.bulk_update(lines, ["product", "variant", "description", "unit_price", "discount_amount", "tax_amount", "total"])
        subscription.save()
    SubscriptionEvent.objects.create(subscription=subscription, actor=user, message=f"Change to {change.plan.name} {change.status}")
    return change


def activate_due(today=None):
    today = today or timezone.localdate()
    count = 0
    for subscription in Subscription.objects.filter(status="confirmed", start_date__lte=today):
        activate(None, subscription)
        count += 1
    return count


def close_expired(today=None):
    today = today or timezone.localdate()
    due = Subscription.objects.filter(status="active", plan__auto_close=True, expiry_date__lt=today)
    count = 0
    for subscription in due.select_related("plan"):
        with transaction.atomic():
            locked = _locked(subscription)
            locked.next_billing_date = None
            locked.closed_at = timezone.now()
            old = locked.status
            locked.status = "closed"
            locked.save()
            SubscriptionEvent.objects.create(subscription=locked, from_status=old, to_status="closed", message="Closed automatically at expiry")
            notify(locked.customer.user, "subscription_expired", f"Subscription {locked.number} has ended")
        count += 1
    return count


def remind_upcoming(today=None, days=7):
    today = today or timezone.localdate()
    target = today + timedelta(days=days)
    subscriptions = Subscription.objects.filter(status="active", expiry_date=target).select_related("customer__user")
    for subscription in subscriptions:
        notify(subscription.customer.user, "upcoming_renewal", f"Subscription {subscription.number} ends on {target}")
    return len(subscriptions)
