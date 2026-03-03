import uuid
import os
from datetime import timedelta
from django.conf import settings
from django.db import models
from minio import Minio
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


# --- 1. 模型定义 ---
class Files(models.Model):
    name = models.CharField(max_length=255, verbose_name="文件名")
    minio_key = models.CharField(max_length=512, unique=True, verbose_name="MinIO路径")
    file_size = models.BigIntegerField(verbose_name="字节大小")
    extension = models.CharField(max_length=20, verbose_name="后缀")
    upload_status = models.IntegerField(
        choices=[(0, '上传中'), (1, '已完成'), (-1, '失败')],
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 修正拼写

    class Meta:
        verbose_name = "图纸文档"
        db_table = "plm_files"  # 建议指定表名


# --- 2. MinIO 公共服务类 ---
class MinioHandler:
    """封装 MinIO 公共操作"""

    def __init__(self):
        # 建议在 settings 中设置 MINIO_SECURE (True/False)
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=getattr(settings, 'MINIO_USE_HTTPS', False)
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME

    def get_upload_url(self, object_name, expires_min=15):
        return self.client.presigned_put_object(
            self.bucket_name, object_name, expires=timedelta(minutes=expires_min)
        )

    def check_exists(self, object_name):
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except Exception:
            return False


# 实例化全局公共服务，复用连接池
minio_service = MinioHandler()


# --- 3. API 视图 ---
class MinioUploadActionView(APIView):
    """步骤 1: 申请上传"""

    def post(self, request):
        file_name = request.data.get('file_name')
        file_size = request.data.get('file_size')

        if not file_name:
            return Response({"error": "参数 file_name 缺失"}, status=status.HTTP_400_BAD_REQUEST)

        # 健壮的后缀提取
        _, ext = os.path.splitext(file_name)
        ext = ext.lstrip('.')

        # 存储路径规划: 业务分类/年/月/日/uuid.ext
        object_name = f"plm/{uuid.uuid4().hex}.{ext}"

        upload_url = minio_service.get_upload_url(object_name)

        doc = Files.objects.create(
            name=file_name,
            minio_key=object_name,
            file_size=file_size or 0,
            extension=ext,
            upload_status=0
        )

        return Response({
            "id": doc.id,
            "upload_url": upload_url,
            "object_name": object_name
        })


class MinioConfirmView(APIView):
    """步骤 2: 确认结果"""

    def post(self, request):
        doc_id = request.data.get('id')
        action = request.data.get('action', 'success')  # 允许前端反馈失败情况

        try:
            doc = Files.objects.get(id=doc_id)

            if action == 'error':
                doc.upload_status = -1
                doc.save()
                return Response({"msg": "已标记为上传失败"})

            if minio_service.check_exists(doc.minio_key):
                doc.upload_status = 1
                doc.save()
                return Response({"status": "success", "msg": "文件已存档"})

            return Response({"error": "MinIO 中未发现该文件"}, status=status.HTTP_400_BAD_REQUEST)

        except Files.DoesNotExist:
            return Response({"error": "记录不存在"}, status=status.HTTP_404_NOT_FOUND)
