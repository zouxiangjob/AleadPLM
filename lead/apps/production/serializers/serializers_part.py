from django.db import transaction
from rest_framework import serializers

from lead.apps.production.models import Files, Mpart, BomItem
from lead.apps.production.serializers.serializers_bom import BomItemSerializer


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Files
        fields = ['name', 'attachment']


class MpartSerializer(serializers.ModelSerializer):
    # 修改为可读写，以便接收前端从 Minio 拿到的文件信息
    files = FileSerializer(many=True, required=False)
    # 维持之前的 JSONField 优化，用于处理复杂的 BOM 写入
    bom_items = serializers.JSONField(required=False)

    class Meta:
        model = Mpart
        fields = '__all__'
        read_only_fields = ['id']

    def to_representation(self, instance):
        """优化查询：使用 values 获取 BOM，使用 prefetch 获取文件"""
        data = super().to_representation(instance)
        # 1. 批量获取 BOM 详情
        data['bom_items'] = BomItem.objects.filter(pid=instance).values(
            'id', 'cid_id', 'cid__code', 'cid__name', 'cid__unit', 'quantity'
        )
        return data

    def _validate_and_get_cids(self, bom_items):
        """提取 BOM 校验逻辑"""
        if not bom_items: return {}
        cid_ids = {item['cid'] for item in bom_items}
        mparts = Mpart.objects.in_bulk(cid_ids)
        missing = cid_ids - set(mparts.keys())
        if missing:
            raise serializers.ValidationError(f"组件不存在: {', '.join(map(str, missing))}")
        return mparts

    @transaction.atomic
    def create(self, validated_data):
        # 1. 提取嵌套数据
        files_data = validated_data.pop('files', [])
        bom_items = validated_data.pop('bom_items', [])

        # 2. 创建主表 Mpart
        mpart = Mpart.objects.create(**validated_data)

        # 3. 批量创建文件记录 (前端已传至 Minio，此处仅存记录)
        if files_data:
            Files.objects.bulk_create([
                Files(mpart=mpart, **item) for item in files_data
            ])

        # 4. 批量创建 BOM 关系
        if bom_items:
            mparts_map = self._validate_and_get_cids(bom_items)
            BomItem.objects.bulk_create([
                BomItem(pid=mpart, cid=mparts_map[item['cid']], quantity=item.get('quantity', 1))
                for item in bom_items
            ])
        return mpart

    @transaction.atomic
    def update(self, instance, validated_data):
        files_data = validated_data.pop('files', None)
        bom_items = validated_data.pop('bom_items', None)

        # 更新基础字段
        instance = super().update(instance, validated_data)

        # 1. 处理文件更新（采用覆盖式：删除旧的，创建新的）
        if files_data is not None:
            instance.files.all().delete()
            Files.objects.bulk_create([
                Files(mpart=instance, **item) for item in files_data
            ])

        # 2. 处理 BOM 更新
        if bom_items is not None:
            instance.pid.all().delete()
            mparts_map = self._validate_and_get_cids(bom_items)
            BomItem.objects.bulk_create([
                BomItem(pid=instance, cid=mparts_map[item['cid']], quantity=item.get('quantity', 1))
                for item in bom_items
            ])
        return instance