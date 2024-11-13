# myapp/permissions.py

from rest_framework.permissions import BasePermission
from rest_framework import exceptions
from django.contrib.auth.models import User

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user