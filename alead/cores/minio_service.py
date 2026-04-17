"""
MinIO 辅助服务模块

本模块封装了与 MinIO 存储交互的辅助类与 REST API 视图：
- 提供读取 Django 配置的 `MinioConfig`，并进行基本校验。
- 提供 `MinioHandler` 封装 MinIO 客户端的常用操作（生成上传 URL、检查对象是否存在）。
- 提供按需单例获取 minio 服务的 `get_minio_service`，支持注入 mock client 以便单元测试。
- 提供两个 DRF 视图用于前端：申请上传（生成 presigned URL）和确认上传结果。

该文件在无法加载真实 `Files` 模型时提供了一个轻量回退实现，便于在不完整环境或单元测试环境下避免导入错误。
"""

import uuid
import os
from datetime import timedelta
from django.conf import settings
from minio import Minio
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ImproperlyConfigured
from django.apps import apps


def get_files_model():
    """
    尝试通过 Django 的 app registry 动态获取 `Files` 模型。

    返回值：
      - 成功时返回真实的模型类（可以使用 .objects.create/.get 等操作）。
      - 失败时返回一个轻量的回退类 `_Fallback`，其仅实现本模块所需的接口并在调用时抛出明确错误。

    设计意图：避免在模块导入阶段因为模型不可用而导致整个模块崩溃（例如在某些测试或外部脚本运行时）。
    """
    try:
        return apps.get_model('alead.apps.production', 'Files')
    except Exception:
        # 回退实现：仅提供模块中使用的最小 API（objects.create/objects.get），并抛出可识别的异常。
        class _Fallback:
            class DoesNotExist(Exception):
                pass

            class _Objects:
                def create(self, *args, **kwargs):
                    raise RuntimeError("Files model is not available in this environment")

                def get(self, *args, **kwargs):
                    raise _Fallback.DoesNotExist("Files model is not available in this environment")

            objects = _Objects()

        return _Fallback


# 注意：原来的 .env 自动加载逻辑已移到 settings 中，MinioConfig 直接从 settings 获取字段。
class MinioConfig:
    """
    从 Django settings 中读取 MinIO 配置并进行简单校验。

    属性：
      - ENDPOINT: MinIO 服务地址（host:port 或域名）
      - ACCESS_KEY / SECRET_KEY: 访问凭证
      - BUCKET_NAME: 使用的存储桶名
      - USE_HTTPS: 是否使用 HTTPS（布尔）
      - UPLOAD_EXPIRES_MINUTES: 预签名上传 URL 的过期时间（分钟）
      - OBJECT_PREFIX: 对象在 bucket 内的前缀（统一规范化为 '' 或以 '/' 结尾的前缀）

    在初始化时会检测 ENDPOINT/ACCESS_KEY/SECRET_KEY/BUCKET_NAME 是否存在，若缺失则抛出 ImproperlyConfigured。
    """
    def __init__(self):
        self.ENDPOINT = getattr(settings, 'MINIO_ENDPOINT', None)
        self.ACCESS_KEY = getattr(settings, 'MINIO_ACCESS_KEY', None)
        self.SECRET_KEY = getattr(settings, 'MINIO_SECRET_KEY', None)
        self.BUCKET_NAME = getattr(settings, 'MINIO_BUCKET_NAME', None)
        self.USE_HTTPS = getattr(settings, 'MINIO_USE_HTTPS', False)
        self.UPLOAD_EXPIRES_MINUTES = getattr(settings, 'MINIO_UPLOAD_EXPIRES_MINUTES', 15)
        self.OBJECT_PREFIX = getattr(settings, 'MINIO_OBJECT_PREFIX', 'plm/')

        # 规范化对象前缀为 '' 或 'prefix/'（去除首尾空白并确保以 '/' 结尾）
        if self.OBJECT_PREFIX is None:
            self.OBJECT_PREFIX = ''
        prefix = str(self.OBJECT_PREFIX).strip()
        if prefix == '':
            self.OBJECT_PREFIX = ''
        else:
            self.OBJECT_PREFIX = prefix.rstrip('/') + '/'

        # 简单校验必需配置项，若缺失则提示明确的配置信息
        missing = [name for name in ('ENDPOINT', 'ACCESS_KEY', 'SECRET_KEY', 'BUCKET_NAME')
                   if not getattr(self, name)]
        if missing:
            raise ImproperlyConfigured(f"Missing MinIO configuration: {', '.join(missing)}")


# --- 2. MinIO 公共服务类 ---
class MinioHandler:
    """
    封装 MinIO 常用操作的轻量类。

    构造：
      - config: 可选，传入 MinioConfig 实例（若不提供会内部创建）
      - client: 可选，传入一个已初始化的 Minio 客户端对象（便于测试时注入 mock）

    常用方法：
      - get_upload_url(object_name, expires_min=None): 生成 presigned PUT URL
      - check_exists(object_name): 检查指定对象是否存在（返回布尔）
    """
    def __init__(self, config=None, client=None):
        # 支持外部传入配置或内部创建
        self.config = config or MinioConfig()

        # 支持注入一个 mock client（方便单元测试）
        if client is not None:
            self.client = client
        else:
            self.client = Minio(
                self.config.ENDPOINT,
                access_key=self.config.ACCESS_KEY,
                secret_key=self.config.SECRET_KEY,
                secure=self.config.USE_HTTPS
            )
        self.bucket_name = self.config.BUCKET_NAME

    def get_upload_url(self, object_name, expires_min=None):
        """
        生成一个 presigned PUT URL，前端可直接向该 URL 上传文件。

        参数：
          - object_name: 存储在 bucket 中的对象 key（含前缀）
          - expires_min: 可选，覆盖配置中的过期分钟数

        返回值：presigned put URL（字符串）
        """
        if expires_min is None:
            expires_min = self.config.UPLOAD_EXPIRES_MINUTES
        return self.client.presigned_put_object(
            self.bucket_name, object_name, expires=timedelta(minutes=expires_min)
        )

    def check_exists(self, object_name):
        """
        检查对象是否存在于 bucket 中。

        返回：True 表示存在，False 表示不存在或发生错误（调用方仅关心存在与否）。
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except Exception:
            return False


# 移除模块导入时立即实例化配置/服务（避免导入失败）
# 提供按需单例获取方法
_MINIO_SERVICE = None


def get_minio_service(client=None):
    """
    返回单例的 MinioHandler 实例。

    设计说明：
      - 延迟初始化（第一次调用时创建），避免在 Django 启动或管理命令导入时强制连接 MinIO。
      - 支持通过 `client` 参数注入一个 mock/minimal 客户端（仅在测试时使用）。
    """
    global _MINIO_SERVICE
    if _MINIO_SERVICE is None:
        cfg = MinioConfig()
        _MINIO_SERVICE = MinioHandler(cfg, client=client)
    return _MINIO_SERVICE


# --- 3. API 视图 ---
class MinioUploadActionView(APIView):
    """
    步骤 1: 申请上传（前端调用）

    请求：POST，JSON body 包含：
      - file_name: 原始文件名（必需）
      - file_size: 可选，文件大小（字节）

    响应：
      - id: 在本地数据库创建的 Files 记录 id
      - upload_url: pre-signed put URL，前端可直接上传
      - object_name: 实际在 MinIO 中的对象 key

    主要流程：
      1. 校验 file_name
      2. 从 file_name 中提取后缀并生成唯一 object_name（使用 uuid）
      3. 通过 MinIO 客户端生成 presigned put URL
      4. 在本地文件表创建一条记录（upload_status 初始为 0）
    """
    def post(self, request):
        file_name = request.data.get('file_name')
        file_size = request.data.get('file_size')

        if not file_name:
            return Response({"error": "参数 file_name 缺失"}, status=status.HTTP_400_BAD_REQUEST)

        # 健壮的后缀提取
        _, ext = os.path.splitext(file_name)
        ext = ext.lstrip('.')

        # 按需获取 minio 服务
        minio_service = get_minio_service()

        # 存储路径规划: 使用配置中的前缀 + uuid.ext
        object_name = f"{minio_service.config.OBJECT_PREFIX}{uuid.uuid4().hex}.{ext}"

        upload_url = minio_service.get_upload_url(object_name)

        Files = get_files_model()
        doc = Files.objects.create(
            name=file_name,
            minio_key=object_name,
            file_size=file_size or 0,
            extension=ext,
            upload_status=0
        )

        return Response({
            "id": getattr(doc, 'id', None),
            "upload_url": upload_url,
            "object_name": object_name
        })


class MinioConfirmView(APIView):
    """
    步骤 2: 前端确认上传结果（或服务器端轮询确认）

    请求：POST，JSON body 包含：
      - id: Files 表中的记录 id
      - action: 可选，'success'（默认）或 'error'，允许前端报告上传失败

    逻辑：
      - 若 action == 'error'，则将记录标记为上传失败（upload_status = -1）
      - 否则调用 minio 服务检查对象是否存在：
          - 若存在则将 upload_status 设为 1（已归档）
          - 若不存在则返回 400 错误，提示 MinIO 中未发现该文件
    """

    def post(self, request):
        doc_id = request.data.get('id')
        action = request.data.get('action', 'success')  # 允许前端反馈失败情况

        Files = get_files_model()
        try:
            doc = Files.objects.get(id=doc_id)

            if action == 'error':
                doc.upload_status = -1
                doc.save()
                return Response({"msg": "已标记为上传失败"})

            minio_service = get_minio_service()
            if minio_service.check_exists(doc.minio_key):
                doc.upload_status = 1
                doc.save()
                return Response({"status": "success", "msg": "文件已存档"})

            return Response({"error": "MinIO 中未发现该文件"}, status=status.HTTP_400_BAD_REQUEST)

        except Files.DoesNotExist:
            return Response({"error": "记录不存在"}, status=status.HTTP_404_NOT_FOUND)
