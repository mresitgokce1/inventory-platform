"""Store URL configuration."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoreViewSet

app_name = 'stores'

router = DefaultRouter()
router.register(r'stores', StoreViewSet)

urlpatterns = [
    path('', include(router.urls)),
]