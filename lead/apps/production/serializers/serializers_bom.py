import re
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers
from lead.apps.production.models import Mpart, BomItem


class BomItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BomItem
        fields = '__all__'


# 重新创建产品
class BomItemInputSerializer(serializers.Serializer):
    cid = serializers.UUIDField(help_text="组件 Product 的 UUID")
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))


class MpartBomSerializer(serializers.ModelSerializer):
    bom_items = BomItemInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Mpart
        fields = '__all__'
        read_only_fields = ['id']

    
    def to_representation(self, instance):
        data = super().to_representation(instance)

        qs = BomItem.objects.filter(pid=instance).select_related('cid')

        bom_items = []
        for item in qs:
            bom_items.append({
                'id': str(item.id),  # 补充BOM项自身ID，用于树形构建
                'cid': str(item.cid_id),
                'code':str(item.cid.code),
                'name':str(item.cid.name),
                'unit': str(item.cid.unit),
                'quantity': str(item.quantity),
            })
        data['bom_items'] = bom_items
        return data

    @transaction.atomic
    def create(self, validated_data):

        bom_items = validated_data.pop('bom_items', [])
        mpart = Mpart.objects.create(**validated_data)

        if not bom_items:
            return mpart

        # 1. 验证所有组件是否存在（包括子组件和父组件）
        all_ids = set()
        for item in bom_items:
            all_ids.add(item['cid'])
            if item.get('pid'):
                all_ids.add(item['pid'])

        exist_products = Mpart.objects.filter(id__in=all_ids)

        # 检查缺失的组件
        have_ids = set()
        for item in exist_products:
            id = item.id
            have_ids.add(id)

        no_ids = all_ids - have_ids
        if no_ids.__len__() != 0:
            raise serializers.ValidationError(
                f"以下组件不存在，请检查：{', '.join(no_ids)}"
            )

        # 创建bom关系
        for item in bom_items:
            son = Mpart.objects.get(id=item['cid'])
            bom = BomItem.objects.create(
                cid=son,
                quantity=item.get('quantity', 1),
                pid=mpart
            )
        return mpart

    @transaction.atomic
    def update(self, instance, validated_data):
        bom_items = validated_data.pop('bom_items', None)

        # 更新 Mpart 本身字段（支持 partial）
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 如果 bom_items 被提供，则更新 BOM 结构
        if bom_items is not None:
            # 清除旧 BOM 项
            BomItem.objects.filter(pid=instance).delete()

            # 验证组件是否存在
            ids = set(item['cid'] for item in bom_items)
            exist_ids = set(str(p.id) for p in Mpart.objects.filter(id__in=ids))
            missing_ids = [str(i) for i in ids if str(i) not in exist_ids]
            if missing_ids:
                raise serializers.ValidationError(f"以下组件不存在，请检查：{', '.join(missing_ids)}")

            # 创建新的 BOM 项
            cid_map = {str(p.id): p for p in Mpart.objects.filter(id__in=ids)}
            bom_objects = [
                BomItem(cid=cid_map[str(item['cid'])], quantity=item.get('quantity', 1), pid=instance)
                for item in bom_items
            ]
            BomItem.objects.bulk_create(bom_objects)

        return instance
