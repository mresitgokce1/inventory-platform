"""Serializers for inventory models."""

from apps.products.serializers import ProductSerializer
from apps.stores.serializers import StoreSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ProductStore, StockMovement

User = get_user_model()


class ProductStoreSerializer(serializers.ModelSerializer):
    """Serializer for ProductStore model."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    store_name = serializers.CharField(source="store.name", read_only=True)
    store_code = serializers.CharField(source="store.code", read_only=True)
    brand_name = serializers.CharField(source="product.brand.name", read_only=True)
    available_quantity = serializers.ReadOnlyField()
    is_below_minimum = serializers.ReadOnlyField()

    class Meta:
        model = ProductStore
        fields = [
            "id",
            "product",
            "product_name",
            "product_sku",
            "store",
            "store_name",
            "store_code",
            "brand_name",
            "quantity_on_hand",
            "reserved_quantity",
            "minimum_stock_level",
            "available_quantity",
            "is_below_minimum",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        """Validate ProductStore data."""
        product = attrs.get("product")
        store = attrs.get("store")
        reserved_quantity = attrs.get("reserved_quantity", 0)
        quantity_on_hand = attrs.get("quantity_on_hand", 0)

        # Validate product and store belong to same brand
        if product and store:
            if product.brand_id != store.brand_id:
                raise serializers.ValidationError(
                    {"product": "Product and Store must belong to the same brand."}
                )

        # Validate reserved quantity
        if reserved_quantity > quantity_on_hand:
            raise serializers.ValidationError(
                {"reserved_quantity": "Reserved quantity cannot exceed quantity on hand."}
            )

        return attrs


class ProductStoreDetailSerializer(ProductStoreSerializer):
    """Detailed serializer with nested product and store information."""

    product = ProductSerializer(read_only=True)
    store = StoreSerializer(read_only=True)

    class Meta(ProductStoreSerializer.Meta):
        fields = ProductStoreSerializer.Meta.fields


class StockMovementSerializer(serializers.ModelSerializer):
    """Serializer for StockMovement model."""

    product_name = serializers.CharField(source="product_store.product.name", read_only=True)
    product_sku = serializers.CharField(source="product_store.product.sku", read_only=True)
    store_name = serializers.CharField(source="product_store.store.name", read_only=True)
    store_code = serializers.CharField(source="product_store.store.code", read_only=True)
    brand_name = serializers.CharField(source="product_store.product.brand.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    # For transfers
    destination_store_name = serializers.CharField(
        source="destination_product_store.store.name", read_only=True
    )
    destination_store_code = serializers.CharField(
        source="destination_product_store.store.code", read_only=True
    )

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product_store",
            "product_name",
            "product_sku",
            "store_name",
            "store_code",
            "brand_name",
            "movement_type",
            "quantity",
            "reference_number",
            "notes",
            "created_by",
            "created_by_name",
            "destination_product_store",
            "destination_store_name",
            "destination_store_code",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        """Validate StockMovement data."""
        movement_type = attrs.get("movement_type")
        quantity = attrs.get("quantity")
        product_store = attrs.get("product_store")
        destination_product_store = attrs.get("destination_product_store")

        # Validate quantity based on movement type
        if movement_type == StockMovement.INBOUND and quantity <= 0:
            raise serializers.ValidationError(
                {"quantity": "Inbound movements must have positive quantity."}
            )

        if movement_type == StockMovement.OUTBOUND and quantity >= 0:
            raise serializers.ValidationError(
                {"quantity": "Outbound movements must have negative quantity."}
            )

        # Validate transfers
        if movement_type == StockMovement.TRANSFER:
            if not destination_product_store:
                raise serializers.ValidationError(
                    {"destination_product_store": "Transfer movements require a destination."}
                )

            if product_store and destination_product_store:
                if product_store.store == destination_product_store.store:
                    raise serializers.ValidationError(
                        {"destination_product_store": "Cannot transfer to the same store."}
                    )

                if product_store.product != destination_product_store.product:
                    raise serializers.ValidationError(
                        {"destination_product_store": "Transfer must be for the same product."}
                    )

        # Validate sufficient stock for outbound and transfers
        if product_store and quantity < 0:  # Outbound movements have negative quantity
            available = product_store.available_quantity
            required = abs(quantity)
            if required > available:
                raise serializers.ValidationError(
                    {
                        "quantity": f"Insufficient stock. Available: {available}, Requested: {required}"
                    }
                )

        return attrs

    def create(self, validated_data):
        """Create stock movement and set created_by from request user."""
        request = self.context.get("request")
        if request and request.user:
            validated_data["created_by"] = request.user
        return super().create(validated_data)


class StockMovementDetailSerializer(StockMovementSerializer):
    """Detailed serializer with nested ProductStore information."""

    product_store = ProductStoreSerializer(read_only=True)
    destination_product_store = ProductStoreSerializer(read_only=True)

    class Meta(StockMovementSerializer.Meta):
        fields = StockMovementSerializer.Meta.fields
