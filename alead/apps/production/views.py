from rest_framework import viewsets
from alead.apps.production.models import BomItem
from alead.apps.production.serializers.serializers_bom import BomItemSerializer


class BomItemViewSet(viewsets.ModelViewSet):
    queryset = BomItem.objects.select_related('pid')
    serializer_class = BomItemSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        mpart_id = self.request.query_params.get('mpart')
        if mpart_id:
            qs = qs.filter(mpart_id=mpart_id)
        return qs


