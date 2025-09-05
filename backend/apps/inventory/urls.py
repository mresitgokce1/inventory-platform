"""Inventory URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProductStoreViewSet, StockMovementViewSet

app_name = "inventory"

router = DefaultRouter()
router.register(r"product-stores", ProductStoreViewSet)
router.register(r"stock-movements", StockMovementViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
