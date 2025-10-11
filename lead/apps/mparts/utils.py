from django.conf import settings
import os

def handle_chunked_upload(upload):
    # 合并分块文件
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'chunks', upload.upload_id)
    final_path = os.path.join(settings.MEDIA_ROOT, 'documents', upload.file_name)

    with open(final_path, 'wb') as output:
        for i in range(upload.total_chunks):
            chunk_path = os.path.join(upload_dir, f'chunk_{i}')
            with open(chunk_path, 'rb') as chunk_file:
                output.write(chunk_file.read())
            os.remove(chunk_path)
    os.rmdir(upload_dir)
    return final_path