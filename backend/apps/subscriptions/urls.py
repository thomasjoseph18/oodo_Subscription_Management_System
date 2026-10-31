from rest_framework.routers import DefaultRouter

from .views import PlanChangeViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register("subscriptions", SubscriptionViewSet, basename="subscription")
router.register("plan-changes", PlanChangeViewSet)
urlpatterns = router.urls
