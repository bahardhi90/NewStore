from rest_framework.routers import SimpleRouter

from .views import CategoryViewSet, CollectionViewSet, ProductViewSet

router = SimpleRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("collections", CollectionViewSet, basename="collection")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls
