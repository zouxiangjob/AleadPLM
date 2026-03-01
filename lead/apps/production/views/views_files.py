from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from lead.apps.production.serializers.serializers_files import FileUploadSerializer


class MinioUploadView(APIView):
    parser_classes = [MultiPartParser] # 必须包含此解析器处理文件

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=201)
        return Response(serializer.errors, status=400)