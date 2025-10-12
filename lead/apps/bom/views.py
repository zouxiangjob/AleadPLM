from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="id",
            type=OpenApiTypes.STR,   # 改成普通字符串
            location=OpenApiParameter.PATH,
            description="可以是 32 位或 36 位 UUID"
        )
    ]
)

class ProductBomViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
