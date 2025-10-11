from rest_framework import serializers
from django.db import transaction
from .models import Product, BomItem

class ProductSerializer(serializers.ModelSerializer):
    # 写入时接收扁平数组（含 parent_component）
    bom_items = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)

    class Meta:
        model = Product
        fields = ['id','code','name','description','bom_items']

    def to_representation(self, instance):
        """
        输出：
        - product 基本信息
        - bom_items: 扁平数组（含 parent_component）
        - bom_tree: 树形结构
        """
        data = super().to_representation(instance)

        # 取所有 BOM 项，并附带组件信息
        qs = BomItem.objects.filter(product=instance).select_related('component', 'parent')

        # 扁平数组
        flat = []
        for item in qs:
            flat.append({
                'id': item.id,
                'component': item.component.id,
                'component_code': item.component.code,
                'component_name': item.component.name,
                'quantity': item.quantity,
                'parent': item.parent_id,
                'parent_component': item.parent.component.id if item.parent_id else None
            })

        # parent_id (BomItem.id) -> children 映射
        children_map = {}
        for i in flat:
            pid = i['parent'] or 0
            children_map.setdefault(pid, []).append(i)

        # 递归构建树（树节点以组件 Product 作为节点）
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
        """
        接收：bom_items = [{component, quantity, parent_component?}]
        步骤：
        1. 创建 Product
        2. 先创建一级（parent_component=None）的 BomItem
        3. 再创建非一级的 BomItem：根据 parent_component 找到父 BomItem
        """
        bom_items = validated_data.pop('bom_items', [])
        product = Product.objects.create(**validated_data)

        # 先按层级分组
        top_level = [i for i in bom_items if not i.get('parent_component')]
        others = [i for i in bom_items if i.get('parent_component')]

        # 创建一级
        top_created = []
        for i in top_level:
            bi = BomItem.objects.create(
                product=product,
                component_id=i['component'],
                quantity=i.get('quantity', 1),
                parent=None
            )
            top_created.append(bi)

        # 为快速查找父关系，构建 (component_id) -> BomItem
        # 注意：若同一组件在不同父下重复，需要 (parent_component, component) 组合键；这里简化为 component 唯一
        component_to_bom = {bi.component_id: bi for bi in top_created}

        # 创建非一级：先确保父 BomItem 存在（parent_component 必须在 top_level 或已创建）
        created = []
        # 为了支持多层级，循环直到无法继续（防止父在下层的情况）
        pending = others[:]
        max_iters = len(pending) + 5
        iters = 0
        while pending and iters < max_iters:
            rest = []
            for i in pending:
                parent_comp = i['parent_component']
                parent_bi = component_to_bom.get(parent_comp)
                if parent_bi:
                    bi = BomItem.objects.create(
                        product=product,
                        component_id=i['component'],
                        quantity=i.get('quantity', 1),
                        parent=parent_bi
                    )
                    created.append(bi)
                    component_to_bom[bi.component_id] = bi
                else:
                    rest.append(i)
            if len(rest) == len(pending):  # 无法前进
                break
            pending = rest
            iters += 1

        if pending:
            raise serializers.ValidationError('存在无法解析的父子关系，请检查 parent_component 是否正确')

        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        高效差异更新（bulk），输入同 create：
        bom_items = [{id?, component, quantity, parent_component?}]
        - 建立目标集合，以 (component, parent_component) 作为匹配键（避免依赖 id）
        - 找出需要新增、更新、删除的项
        - 批量执行，保持原子性
        """
        bom_items = validated_data.pop('bom_items', [])

        # 更新产品基本信息
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        # 现有 BOM
        old_qs = list(BomItem.objects.filter(product=instance).select_related('component', 'parent'))

        # 构造父映射：通过组件 id 找到对应的 BomItem（顶层和已存在的）
        # 注意：若同一组件在不同父下出现，需要 (parent_component, component) 做键
        def key_of(bi):
            return (bi.component_id, bi.parent.component_id if bi.parent_id else None)

        old_map = {key_of(bi): bi for bi in old_qs}

        # 目标集合（输入）
        target_items = []
        for i in bom_items:
            target_items.append((
                i['component'],
                i.get('parent_component') or None,
                i.get('quantity', 1),
                i.get('id', None)
            ))

        # 收集顶层父组件 id（便于先创建/校验）
        top_components = {comp for comp, parent_comp, *_ in target_items if parent_comp is None}

        # 预先确保顶层存在于 old_map 中，不存在则标记新增
        to_create = []
        to_update = []
        seen_keys = set()

        # 一轮创建/更新：需要先处理顶层，再处理次级（简单实现：循环两次）
        for pass_idx in (0, 1):
            for comp, parent_comp, qty, _id in target_items:
                is_top = parent_comp is None
                if pass_idx == 0 and not is_top:
                    continue
                if pass_idx == 1 and is_top:
                    continue

                k = (comp, parent_comp)
                seen_keys.add(k)

                existing = old_map.get(k)
                if existing:
                    if existing.quantity != qty:
                        existing.quantity = qty
                        to_update.append(existing)
                else:
                    # 解析父 BomItem
                    parent_bi = None
                    if parent_comp is not None:
                        parent_bi = old_map.get((parent_comp, None))  # 父为顶层
                        if not parent_bi:
                            # 如果父不是顶层，则尝试在 old_map 查找任意父组合（此处可扩展更复杂层级）
                            parent_bi = next((bi for (c, p), bi in old_map.items() if c == parent_comp), None)
                    bi = BomItem(product=instance, component_id=comp, quantity=qty, parent=parent_bi)
                    to_create.append(bi)
                    # 先加入 old_map，便于后续子层匹配
                    old_map[k] = bi

        # 批量创建/更新
        if to_create:
            BomItem.objects.bulk_create(to_create)
        if to_update:
            BomItem.objects.bulk_update(to_update, ['quantity'])

        # 删除旧的但不在目标集合里的项
        to_delete = []
        for k, bi in old_map.items():
            if k not in seen_keys:
                # 仅删除数据库已有项（bulk_create 后的新对象也在 old_map，但已存在于 seen_keys 的会保留）
                if bi.id:
                    to_delete.append(bi.id)
        if to_delete:
            BomItem.objects.filter(id__in=to_delete).delete()

        return instance
