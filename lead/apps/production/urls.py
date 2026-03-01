from django.urls import path, include
from rest_framework.routers import DefaultRouter
from lead.apps.production.views.views_bom import MpartBomViewSet, BomItemViewSet

router = DefaultRouter()

router.register(r'mpart', MpartBomViewSet, basename='mpart')
router.register(r'bom', BomItemViewSet, basename='bom')


urlpatterns = [
    # path('list', book_list, name='book_list'),
    # path('new', book_create, name='book_create'),
    # path('edit/<int:pk>/', book_update, name='book_update'),
    # path('delete/<int:pk>/', book_delete, name='book_delete'),
    path('', include(router.urls)),
    # path('api/mparts/', BookCreateView.as_view(), name='book-create'),
]




