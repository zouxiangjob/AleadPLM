from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from lead.apps.production.models import Mpart, BomItem
from lead.apps.production.serializers.serializers_bom import MpartBomSerializer, BomItemSerializer
from lead.apps.unit.swagger_params import uuid_path_param, bom_filter_params, pagination_params, filter_params


class MpartBomViewSet(viewsets.ModelViewSet):
    queryset = Mpart.objects.all().order_by('id')
    serializer_class = MpartBomSerializer




class BomItemViewSet(viewsets.ModelViewSet):
    queryset = BomItem.objects.select_related('pid')
    serializer_class = BomItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        mpart_id = self.request.query_params.get('mpart')
        if mpart_id:
            qs = qs.filter(mpart_id=mpart_id)
        return qs

