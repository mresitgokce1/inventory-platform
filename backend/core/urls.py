from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "ok", "env": "dev"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health"),
]
