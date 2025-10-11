from django.conf.urls.static import static
from django.urls import path, include

from lead.apps.mparts.views import MpartViewSet
from lead import settings
# from .views import book_list, book_create, book_update, book_delete, BookCreateView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('mparts', MpartViewSet)

app_name = "mparts"
urlpatterns = [
    # path('list', book_list, name='book_list'),
    # path('new', book_create, name='book_create'),
    # path('edit/<int:pk>/', book_update, name='book_update'),
    # path('delete/<int:pk>/', book_delete, name='book_delete'),
    path('', include(router.urls)),
    # path('api/mparts/', BookCreateView.as_view(), name='book-create'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

