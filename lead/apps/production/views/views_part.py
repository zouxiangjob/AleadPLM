from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics

from lead.apps.production.models import Mpart
from lead.apps.production.serializers.serializers_part import MpartSerializer



class MpartFilter(filters.FilterSet):
    # 明确指定 field_name 指向模型中的 'name' 字段
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

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


class FilterListView(generics.ListAPIView):
    queryset = Mpart.objects.all()
    serializer_class = MpartSerializer
    filter_backends = [DjangoFilterBackend]

    # 绑定上面定义的类
    filterset_class = MpartFilter

