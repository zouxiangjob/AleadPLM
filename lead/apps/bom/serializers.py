from rest_framework import serializers
from django.db import transaction
from .models import Product, BomItem


class BomItemInputSerializer(serializers.Serializer):
    component = serializers.UUIDField(help_text="组件 Product 的 UUID")
    quantity = serializers.IntegerField(required=False, default=1, help_text="数量，默认为 1")
    parent_component = serializers.UUIDField(required=False, allow_null=True, help_text="父组件的 UUID，可为空")


class ProductSerializer(serializers.ModelSerializer):
    # 可选的 BOM 子项
    bom_items = BomItemInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Product
        fields = ['id', 'code', 'name', 'description', 'bom_items']

    def to_representation(self, instance):
        """输出 product 基本信息 + 扁平数组 + 树形结构"""
        data = super().to_representation(instance)

        qs = BomItem.objects.filter(product=instance).select_related('component', 'parent')

        flat = []
        for item in qs:
            flat.append({
                'id': str(item.id),
                'component': str(item.component.id),
                'component_code': item.component.code,
                'component_name': item.component.name,
                'quantity': item.quantity,
                'parent': str(item.parent_id) if item.parent_id else None,
                'parent_component': str(item.parent.component.id) if item.parent_id else None
            })

        children_map = {}
        for i in flat:
            pid = i['parent'] or 0
            children_map.setdefault(pid, []).append(i)

        def build_tree(parent_bom_item_id):
            nodes = []
            for i in children_map.get(parent_bom_item_id, []):
                nodes.append({
                    'id': i['component'],
                    'code': i['component_code'],
                    'name': i['component_name'],
                    'quantity': i['quantity'],
                    'children': build_tree(i['id'])
                })
            return nodes

        data['bom_items'] = flat
        data['bom_tree'] = build_tree(0)
        return data

    @transaction.atomic
    def create(self, validated_data):
        """创建 Product，如果有 bom_items 再处理 BOM"""
        bom_items = validated_data.pop('bom_items', [])
        product = Product.objects.create(**validated_data)

        if not bom_items:
            return product  # 只创建产品，不生成 BOM

        # 如果有 BOM 子项，再走原有逻辑
        top_level = [i for i in bom_items if not i.get('parent_component')]
        others = [i for i in bom_items if i.get('parent_component')]

        component_to_bom = {}
        for i in top_level:
            bi = BomItem.objects.create(
                product=product,
                component_id=i['component'],
                quantity=i.get('quantity', 1),
                parent=None
            )
            component_to_bom[bi.component_id] = bi

        pending = others[:]
        max_iters = len(pending) + 5
        iters = 0
        while pending and iters < max_iters:
            rest = []
            for i in pending:
                parent_comp = i.get('parent_component')
                parent_bi = component_to_bom.get(parent_comp)
                if parent_bi:
                    bi = BomItem.objects.create(
                        product=product,
                        component_id=i['component'],
                        quantity=i.get('quantity', 1),
                        parent=parent_bi
                    )
                    component_to_bom[bi.component_id] = bi
                else:
                    rest.append(i)
            if len(rest) == len(pending):
                break
            pending = rest
            iters += 1

        if pending:
            raise serializers.ValidationError("存在无法解析的父子关系，请检查 parent_component 是否正确")

        return product
