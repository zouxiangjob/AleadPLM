from datetime import timedelta
import shortuuid
from django.conf import settings
from minio import Minio


class MinioService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            conf = settings.MINIO_CONF
            cls._instance.client = Minio(
                endpoint=conf['endpoint'],
                access_key=conf['access_key'],
                secret_key=conf['secret_key'],
                secure=conf.get('secure', False)
            )
            cls._instance.bucket_name = conf['bucket_name']
            # 确保桶存在
            if not cls._instance.client.bucket_exists(cls._instance.bucket_name):
                cls._instance.client.make_bucket(cls._instance.bucket_name)
        return cls._instance

    def upload_file(self, file_obj, folder="uploads"):
        """
        上传 Django 文件对象到 MinIO
        """
        # 生成唯一文件名防止覆盖
        ext = file_obj.name.split('.')[-1]
        file_name = f"{folder}/{shortuuid.uuid.hex}.{ext}"

        # 执行上传
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=file_name,
            data=file_obj,
            length=file_obj.size,
            content_type=file_obj.content_type
        )
        return file_name

    def get_url(self, object_name, expires=timedelta(hours=1)):
        """获取带签名的临时预览链接"""
        return self.client.presigned_get_object(
            self.bucket_name, object_name, expires=expires
        )


minio_service = MinioService()