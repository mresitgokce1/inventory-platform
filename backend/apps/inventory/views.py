from django.shortcuts import render

"""Inventory views for the inventory platform."""
from apps.accounts.roles import BRAND_MANAGER, STAFF, STORE_MANAGER, SYSTEM_ADMIN
from apps.common.permissions import BrandScopedPermission
from django.db.models import F, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ProductStore, StockMovement
from .serializers import (
    ProductStoreDetailSerializer,
    ProductStoreSerializer,
    StockMovementDetailSerializer,
    StockMovementSerializer,
)


class ProductStoreViewSet(viewsets.ModelViewSet):
    """ViewSet for ProductStore model with role-based permissions."""

    queryset = ProductStore.objects.all()
    serializer_class = ProductStoreSerializer
    permission_classes = [BrandScopedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filtering options
    filterset_fields = ["product", "store", "product__brand", "store__brand"]
    search_fields = ["product__name", "product__sku", "store__name", "store__code"]
    ordering_fields = ["quantity_on_hand", "reserved_quantity", "minimum_stock_level", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "retrieve":
            return ProductStoreDetailSerializer
        return ProductStoreSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions and brand scoping."""
        user = self.request.user
        queryset = ProductStore.objects.select_related(
            "product", "product__brand", "store", "store__brand"
        )

        # System admins see all
        if user.is_system_admin():
            return queryset

        # Brand-scoped users see only their brand's data
        user_brand = user.get_brand()
        if user_brand:
            queryset = queryset.filter(product__brand=user_brand)

            # Store managers see only their store's data
            if user.has_role(STORE_MANAGER):
                # Assuming store managers are associated with stores
                # This would need additional user-store relationship in a real system
                pass

        return queryset

    def create(self, request, *args, **kwargs):
        """Handle ProductStore creation with proper permissions."""
        user = request.user

        # Only BRAND_MANAGER and SYSTEM_ADMIN can create inventory records
        if not user.has_role(SYSTEM_ADMIN, BRAND_MANAGER):
            return Response(
                {"detail": "Permission denied", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Handle ProductStore updates with proper permissions."""
        user = request.user

        # STAFF cannot update inventory records
        if user.has_role(STAFF):
            return Response(
                {"detail": "Permission denied", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Handle ProductStore deletion with proper permissions."""
        user = request.user

        # Only BRAND_MANAGER and SYSTEM_ADMIN can delete inventory records
        if not user.has_role(SYSTEM_ADMIN, BRAND_MANAGER):
            return Response(
                {"detail": "Permission denied", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Get products with stock below minimum level."""
        queryset = self.get_queryset().filter(quantity_on_hand__lt=F("minimum_stock_level"))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.ModelViewSet):
    """ViewSet for StockMovement model with role-based permissions."""

    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [BrandScopedPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filtering options
    filterset_fields = [
        "product_store",
        "movement_type",
        "created_by",
        "product_store__product",
        "product_store__store",
        "product_store__product__brand",
    ]
    search_fields = [
        "product_store__product__name",
        "product_store__product__sku",
        "product_store__store__name",
        "reference_number",
        "notes",
    ]
    ordering_fields = ["quantity", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "retrieve":
            return StockMovementDetailSerializer
        return StockMovementSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions and brand scoping."""
        user = self.request.user
        queryset = StockMovement.objects.select_related(
            "product_store",
            "product_store__product",
            "product_store__product__brand",
            "product_store__store",
            "created_by",
            "destination_product_store",
            "destination_product_store__store",
        )

        # System admins see all
        if user.is_system_admin():
            return queryset

        # Brand-scoped users see only their brand's data
        user_brand = user.get_brand()
        if user_brand:
            queryset = queryset.filter(product_store__product__brand=user_brand)

            # Store managers see only their store's data
            if user.has_role(STORE_MANAGER):
                # This would need additional user-store relationship in a real system
                pass

        return queryset

    def create(self, request, *args, **kwargs):
        """Handle StockMovement creation with proper permissions."""
        user = request.user

        # All authenticated users can create stock movements (with brand scoping)
        # But the validation is handled by the serializer and model
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Prevent updates to stock movements (they are immutable)."""
        return Response(
            {"detail": "Stock movements cannot be updated", "code": "METHOD_NOT_ALLOWED"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        """Prevent partial updates to stock movements (they are immutable)."""
        return Response(
            {"detail": "Stock movements cannot be updated", "code": "METHOD_NOT_ALLOWED"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs):
        """Handle StockMovement deletion with proper permissions."""
        user = request.user

        # Only SYSTEM_ADMIN can delete stock movements (for data integrity)
        if not user.has_role(SYSTEM_ADMIN):
            return Response(
                {"detail": "Permission denied", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def by_product(self, request):
        """Get stock movements filtered by product."""
        product_id = request.query_params.get("product_id")
        if not product_id:
            return Response(
                {"detail": "product_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(product_store__product_id=product_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def by_store(self, request):
        """Get stock movements filtered by store."""
        store_id = request.query_params.get("store_id")
        if not store_id:
            return Response(
                {"detail": "store_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(product_store__store_id=store_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
