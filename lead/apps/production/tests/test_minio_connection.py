# 导入 Django 的测试工具类 SimpleTestCase 和 override_settings 装饰器
from django.test import SimpleTestCase, override_settings

# 使用 override_settings 装饰器为测试提供 MinIO 的配置
@override_settings(
    MINIO_ENDPOINT='127.0.0.1:9000',  # MinIO 服务的地址
    MINIO_ACCESS_KEY='admin',         # MinIO 的访问密钥
    MINIO_SECRET_KEY='abc123456',     # MinIO 的密钥
    MINIO_BUCKET_NAME='plm',          # 测试使用的存储桶名称
    MINIO_USE_HTTPS=False             # 是否使用 HTTPS（测试环境为 False）
)
class MinioConnectionTest(SimpleTestCase):
    # 测试是否能够连接到本地 MinIO 服务
    def test_can_connect_local_minio(self):
        # 设置环境变量，确保测试时使用正确的 MinIO 配置
        import os
        os.environ.update({
            'MINIO_ENDPOINT': '127.0.0.1:9000',
            'MINIO_ACCESS_KEY': 'admin',
            'MINIO_SECRET_KEY': 'abc123456',
            'MINIO_BUCKET_NAME': 'plm',
            'MINIO_USE_HTTPS': 'False',
        })

        # 延迟导入 MinioConfig 和 MinioHandler，确保环境变量已生效
        from lead.apps.production.unit.minio_service import MinioConfig, MinioHandler

        try:
            # 初始化 MinIO 配置和处理器
            cfg = MinioConfig()
            handler = MinioHandler(cfg)
            # 测试列出存储桶，验证是否能够成功连接到 MinIO
            buckets = handler.client.list_buckets()
            self.assertIsNotNone(buckets)  # 确保返回的存储桶列表不为空
        except Exception as exc:
            # 如果连接失败，测试失败并输出错误信息
            self.fail(f"无法连接到本地 MinIO：{exc}")
        finally:
            # 清理测试时设置的环境变量
            for k in ('MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'MINIO_BUCKET_NAME', 'MINIO_USE_HTTPS'):
                os.environ.pop(k, None)

    # 测试文件上传和下载功能
    def test_upload_and_download_file(self):
        # 设置环境变量，确保测试时使用正确的 MinIO 配置
        import os
        os.environ.update({
            'MINIO_ENDPOINT': '127.0.0.1:9000',
            'MINIO_ACCESS_KEY': 'admin',
            'MINIO_SECRET_KEY': 'abc123456',
            'MINIO_BUCKET_NAME': 'plm',
            'MINIO_USE_HTTPS': 'False',
        })

        # 导入必要的模块
        import io
        import uuid
        from lead.apps.production.unit.minio_service import MinioConfig, MinioHandler

        try:
            # 初始化 MinIO 配置和处理器
            cfg = MinioConfig()
            handler = MinioHandler(cfg)
            client = handler.client
            bucket = handler.bucket_name

            # 如果存储桶不存在，则创建存储桶
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)

            # 准备测试数据
            data = b"unit-test-minio-upload-download"  # 测试文件内容
            object_name = f"{handler.config.OBJECT_PREFIX}test-{uuid.uuid4().hex}.bin"  # 生成唯一的对象名称
            data_io = io.BytesIO(data)  # 将数据包装为 BytesIO 对象

            # 上传文件到 MinIO
            client.put_object(bucket, object_name, data_io, length=len(data))

            # 下载文件并验证内容
            resp = client.get_object(bucket, object_name)
            downloaded = resp.read()  # 读取下载的内容
            try:
                resp.close()  # 关闭响应
                resp.release_conn()  # 释放连接
            except Exception:
                pass

            # 确保下载的内容与上传的内容一致
            self.assertEqual(downloaded, data, "下载内容与上传内容不一致")

            # 删除测试对象
            try:
                client.remove_object(bucket, object_name)
            except Exception:
                self.fail(f"测试对象删除失败: {object_name}")

        except Exception as exc:
            # 如果上传或下载失败，测试失败并输出错误信息
            self.fail(f"上传/下载测试失败：{exc}")
        finally:
            # 清理测试时设置的环境变量
            for k in ('MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'MINIO_BUCKET_NAME', 'MINIO_USE_HTTPS'):
                os.environ.pop(k, None)
