"""
Root URL configuration.

All authentication-related endpoints live under /api/auth/ and are
defined in authentication/urls.py to keep this file short and clean.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls")),
]
