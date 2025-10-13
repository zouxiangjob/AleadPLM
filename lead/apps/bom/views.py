from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from .models import Product, BomItem
from .serializers import ProductSerializer, BomItemSerializer
from ..unit_configuration.swagger_params import uuid_path_param, bom_filter_params, pagination_params, filter_params


class ProductBomViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class BomItemViewSet(viewsets.ModelViewSet):
    queryset = BomItem.objects.select_related('product', 'component', 'parent')
    serializer_class = BomItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        product_id = self.request.query_params.get('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs
    @extend_schema(parameters=[uuid_path_param])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(parameters=[uuid_path_param])
    def update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(parameters=[uuid_path_param])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(parameters=[uuid_path_param])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(parameters=bom_filter_params + pagination_params + filter_params)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

