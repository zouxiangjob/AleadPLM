from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from .models import Mpart, BomItem
from .serializers import MpartBomSerializer, BomItemSerializer
from ..unit_configuration.swagger_params import uuid_path_param, bom_filter_params, pagination_params, filter_params


class MpartBomViewSet(viewsets.ModelViewSet):
    queryset = Mpart.objects.all().order_by('id')
    serializer_class = MpartBomSerializer

    @extend_schema(parameters=[uuid_path_param])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(parameters=[uuid_path_param])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(parameters=[uuid_path_param])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(parameters=[uuid_path_param])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)



class BomItemViewSet(viewsets.ModelViewSet):
    queryset = BomItem.objects.select_related('pid')
    serializer_class = BomItemSerializer

    @extend_schema(parameters=[uuid_path_param])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(parameters=[uuid_path_param])
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(parameters=[uuid_path_param])
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(parameters=[uuid_path_param])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(parameters=bom_filter_params + pagination_params + filter_params)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        mpart_id = self.request.query_params.get('mpart')
        if mpart_id:
            qs = qs.filter(mpart_id=mpart_id)
        return qs

