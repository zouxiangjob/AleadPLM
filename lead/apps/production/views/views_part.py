from rest_framework import viewsets
from rest_framework.response import Response

from lead.apps.production.models import Mpart
from lead.apps.production.serializers.serializers_part import MpartSerializer


class MpartViewSet(viewsets.ModelViewSet):
    queryset = Mpart.objects.all()
    serializer_class = MpartSerializer

    def perform_create(self, serializer):
        print("perform_create")
        serializer.save()

    def post(self, request):
        print(request.data)
        print("post")
        file_obj = "fileobj"
        return Response({"status": "success", "filename": file_obj})



