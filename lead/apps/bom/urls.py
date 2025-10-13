from rest_framework.routers import DefaultRouter
from .views import ProductBomViewSet, BomItemViewSet

router = DefaultRouter()

router.register(r'bom/products', ProductBomViewSet, basename='product-bom')
router.register(r'bom-items', BomItemViewSet, basename='bom-item')

urlpatterns = router.urls

