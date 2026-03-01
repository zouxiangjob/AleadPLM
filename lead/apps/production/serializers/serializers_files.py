from rest_framework import serializers

from lead.apps.unit.minio_service import minio_service


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    folder = serializers.CharField(required=False, default="general")

    def save(self):
        file_obj = self.validated_data['file']
        folder = self.validated_data['folder']
        # 调用我们的通用服务
        file_path = minio_service.upload_file(file_obj, folder)
        return {
            "file_path": file_path,
            "url": minio_service.get_url(file_path)
        }