from django.http import request
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import generics, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

# from .forms import BookForm
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

