from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PaymentViewSet, RazorpayWebhookView

router = DefaultRouter()
router.register("payments", PaymentViewSet, basename="payment")
urlpatterns = [path("payments/razorpay/webhook/", RazorpayWebhookView.as_view()), *router.urls]
