from django.urls import path, include
from rest_framework.routers import DefaultRouter
from lead.apps.production.views.views_bom import  BomItemViewSet
from lead.apps.production.views.views_part import MpartViewSet

router = DefaultRouter()

router.register(r'mpart', MpartViewSet, basename='mpart')
router.register(r'bom', BomItemViewSet, basename='bom')


urlpatterns = [
    path('', include(router.urls)),
]




