'''
Date: 2024-08-28 19:26:59
LastEditors: 牛智超
LastEditTime: 2024-08-28 20:22:40
FilePath: \国金项目\algo\在网上找的代码\web服务器demo\DjangoDemo\mysite\books\views.py
'''
from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Snippet, Book
from .serializers import SnippetSerializer
from django_filters.rest_framework import DjangoFilterBackend

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user
# Create your views here.
 
def index(request):
    books = Book.objects.all()
    return render(request, 'books/index.html', {'books': books})


class SnippetList(generics.ListCreateAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer

class SnippetDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer
    
# myapp/views.py


class SnippetViewSet(viewsets.ModelViewSet):
    queryset = Snippet.objects.all()
    serializer_class = MyModelSerializer
    permission_classes = [IsOwnerOrReadOnly]
    

class SnippetList(generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['owner', 'created']
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer