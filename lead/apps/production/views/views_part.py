from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics

from lead.apps.production.models import Mpart
from lead.apps.production.serializers.serializers_part import MpartSerializer



class MpartFilter(filters.FilterSet):
    # 如果想模糊查询，用 lookup_expr='icontains'
    name = filters.CharFilter(lookup_expr='icontains')
    class Meta:
        model = Mpart
        fields = ['name']


class MpartViewSet(viewsets.ModelViewSet):
    queryset = Mpart.objects.all()
    serializer_class = MpartSerializer

    # 关键补全：让 ViewSet 也支持查询过滤
    filter_backends = [DjangoFilterBackend]
    filterset_class = MpartFilter

    def perform_create(self, serializer):
        print("perform_create")
        serializer.save()


