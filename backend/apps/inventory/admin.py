from django.contrib import admin

"""Admin interface for inventory models."""
from django.contrib import admin

from .models import ProductStore, StockMovement


@admin.register(ProductStore)
class ProductStoreAdmin(admin.ModelAdmin):
    """Admin interface for ProductStore model."""

    list_display = [
        "product",
        "store",
        "quantity_on_hand",
        "reserved_quantity",
        "minimum_stock_level",
        "is_below_minimum",
        "created_at",
    ]
    list_filter = ["product__brand", "store__brand", "store", "created_at", "updated_at"]
    search_fields = ["product__name", "product__sku", "store__name", "store__code"]
    readonly_fields = ["id", "available_quantity", "is_below_minimum", "created_at", "updated_at"]

    fieldsets = (
        ("Product & Store", {"fields": ("product", "store")}),
        (
            "Inventory",
            {
                "fields": (
                    "quantity_on_hand",
                    "reserved_quantity",
                    "minimum_stock_level",
                    "available_quantity",
                    "is_below_minimum",
                )
            },
        ),
        ("Metadata", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("product", "product__brand", "store", "store__brand")
        )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Admin interface for StockMovement model."""

    list_display = [
        "product_store",
        "movement_type",
        "quantity",
        "reference_number",
        "created_by",
        "created_at",
    ]
    list_filter = [
        "movement_type",
        "product_store__product__brand",
        "product_store__store",
        "created_at",
    ]
    search_fields = [
        "product_store__product__name",
        "product_store__product__sku",
        "product_store__store__name",
        "reference_number",
        "notes",
    ]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        (
            "Movement Details",
            {"fields": ("product_store", "movement_type", "quantity", "reference_number", "notes")},
        ),
        (
            "Transfer Details",
            {
                "fields": ("destination_product_store",),
                "classes": ("collapse",),
                "description": "Only required for transfer movements",
            },
        ),
        (
            "Metadata",
            {"fields": ("created_by", "id", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related(
                "product_store",
                "product_store__product",
                "product_store__store",
                "created_by",
                "destination_product_store",
            )
        )

    def has_change_permission(self, request, obj=None):
        """Prevent editing stock movements (they should be immutable)."""
        return False

    def save_model(self, request, obj, form, change):
        """Set created_by to current user for new movements."""
        if not change:  # Only for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
