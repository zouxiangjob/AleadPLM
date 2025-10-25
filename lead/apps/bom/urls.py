from rest_framework.routers import DefaultRouter
from .views import MpartBomViewSet, BomItemViewSet

router = DefaultRouter()

router.register(r'bom/mpart', MpartBomViewSet, basename='mpart-bom')
router.register(r'bom-items', BomItemViewSet, basename='bom-item')

urlpatterns = router.urls

