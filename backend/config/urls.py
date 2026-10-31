from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.customers.urls")),
    path("api/", include("apps.products.urls")),
    path("api/", include("apps.plans.urls")),
    path("api/", include("apps.taxes.urls")),
    path("api/", include("apps.discounts.urls")),
    path("api/", include("apps.quotations.urls")),
    path("api/", include("apps.subscriptions.urls")),
    path("api/", include("apps.invoices.urls")),
    path("api/", include("apps.payments.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.analytics.urls")),
    path("api/", include("apps.audit_logs.urls")),
]
