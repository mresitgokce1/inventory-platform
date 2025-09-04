from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "ok", "env": "dev"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health"),
    path("api/", include("apps.accounts.urls", namespace="accounts")),
]
