from rest_framework.routers import DefaultRouter

from .views import PaymentTermViewSet, PlanViewSet

router = DefaultRouter()
router.register("plans", PlanViewSet)
router.register("payment-terms", PaymentTermViewSet)
urlpatterns = router.urls
