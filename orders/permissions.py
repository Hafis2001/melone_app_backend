from rest_framework import permissions
from django.conf import settings

class HasAPIKey(permissions.BasePermission):
    """
    Custom permission to only allow access to requests with a valid x-api-key header.
    """
    def has_permission(self, request, view):
        api_key = request.headers.get('x-api-key')
        if not api_key:
            return False
        return api_key == settings.API_SECRET_KEY
