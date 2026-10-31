import hashlib
import hmac

import razorpay
from django.conf import settings

from common.exceptions import BusinessRuleError


def is_enabled():
    return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


def _client():
    if not is_enabled():
        raise BusinessRuleError("Online payments are not configured.", "gateway_disabled")
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_order(amount_paise, receipt, notes=None):
    return _client().order.create({"amount": amount_paise, "currency": "INR", "receipt": receipt, "notes": notes or {}})


def _hmac_hex(secret, message: bytes):
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def verify_checkout_signature(order_id, payment_id, signature):
    if not settings.RAZORPAY_KEY_SECRET or not signature:
        return False
    expected = _hmac_hex(settings.RAZORPAY_KEY_SECRET, f"{order_id}|{payment_id}".encode())
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(body: bytes, signature):
    if not settings.RAZORPAY_WEBHOOK_SECRET or not signature:
        return False
    return hmac.compare_digest(_hmac_hex(settings.RAZORPAY_WEBHOOK_SECRET, body), signature)
