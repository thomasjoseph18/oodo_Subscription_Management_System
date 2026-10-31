from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, VariantViewSet

router = DefaultRouter()
router.register("products", ProductViewSet)
router.register("variants", VariantViewSet)
urlpatterns = router.urls
