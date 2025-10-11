from rest_framework.routers import DefaultRouter
from .views import ProductBomViewSet

router = DefaultRouter()
router.register(r'bom/products', ProductBomViewSet, basename='product-bom')

urlpatterns = router.urls

