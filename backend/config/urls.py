"""
URL configuration for Weather-Aware Truck Routing backend.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("routing.api.urls")),
]
