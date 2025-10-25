from rest_framework import generics, viewsets
from rest_framework.response import Response
from .models import Mpart
from .serializers import MpartsSerializer


class MpartViewSet(viewsets.ModelViewSet):
    queryset = Mpart.objects.all()
    serializer_class = MpartsSerializer

    def perform_create(self, serializer):
        print("perform_create")
        serializer.save()

    def post(self, request):
        print(request.data)
        print("post")
        file_obj = "fileobj"
        return Response({"status": "success", "filename": file_obj})

