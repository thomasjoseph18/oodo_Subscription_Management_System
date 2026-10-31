from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BillingRunViewSet, BillingSettingsView, InvoiceViewSet

router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("billing-runs", BillingRunViewSet)
urlpatterns = [path("settings/", BillingSettingsView.as_view()), *router.urls]
