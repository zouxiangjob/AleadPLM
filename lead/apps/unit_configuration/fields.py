from rest_framework import serializers
import uuid

class FlexibleUUIDField(serializers.UUIDField):
    def to_internal_value(self, data):
        # 自动补连字符
        if isinstance(data, str) and len(data) == 32:
            try:
                data = str(uuid.UUID(data))
            except ValueError:
                pass
        return super().to_internal_value(data)
