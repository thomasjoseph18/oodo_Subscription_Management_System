from rest_framework.routers import DefaultRouter

from .views import QuotationTemplateViewSet, QuotationViewSet

router = DefaultRouter()
router.register("quotation-templates", QuotationTemplateViewSet)
router.register("quotations", QuotationViewSet, basename="quotation")
urlpatterns = router.urls
