from decimal import Decimal

from rest_framework import serializers
from lead.apps.production.models import BomItem


class BomItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BomItem
        fields = '__all__'


# 重新创建产品
class BomItemInputSerializer(serializers.Serializer):
    cid = serializers.CharField(help_text="组件 Product 的 UUID")
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))



