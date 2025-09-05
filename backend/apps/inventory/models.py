"""Inventory models for the inventory platform."""

from apps.common.models import BaseModel
from apps.products.models import Product
from apps.stores.models import Store
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

User = get_user_model()


class ProductStore(BaseModel):
    """Junction model representing product inventory at a specific store."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="store_inventories")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="product_inventories")
    quantity_on_hand = models.PositiveIntegerField(
        default=0, help_text="Current physical stock quantity"
    )
    reserved_quantity = models.PositiveIntegerField(
        default=0, help_text="Quantity reserved for orders"
    )
    minimum_stock_level = models.PositiveIntegerField(
        default=0, help_text="Minimum stock level for reorder alerts"
    )

    class Meta:
        db_table = "inventory_product_store"
        verbose_name = "Product Store Inventory"
        verbose_name_plural = "Product Store Inventories"
        ordering = ["-created_at"]
        unique_together = [("product", "store")]

    def __str__(self):
        return f"{self.product.name} @ {self.store.name} - {self.quantity_on_hand} units"

    @property
    def available_quantity(self):
        """Calculate available quantity (on hand - reserved)."""
        return max(0, self.quantity_on_hand - self.reserved_quantity)

    @property
    def is_below_minimum(self):
        """Check if stock is below minimum level."""
        return self.quantity_on_hand < self.minimum_stock_level

    def clean(self):
        """Custom validation for ProductStore fields."""
        super().clean()

        # Validate that product and store belong to the same brand
        if self.product_id and self.store_id:
            if self.product.brand_id != self.store.brand_id:
                raise ValidationError(
                    {"product": "Product and Store must belong to the same brand."}
                )

        # Validate reserved quantity doesn't exceed on hand quantity
        if self.reserved_quantity > self.quantity_on_hand:
            raise ValidationError(
                {"reserved_quantity": "Reserved quantity cannot exceed quantity on hand."}
            )

    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)


class StockMovement(BaseModel):
    """Model for tracking all inventory movements and changes."""

    # Movement types
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"

    MOVEMENT_TYPE_CHOICES = [
        (INBOUND, "Inbound - Stock received"),
        (OUTBOUND, "Outbound - Stock sold/used"),
        (TRANSFER, "Transfer - Stock moved between stores"),
        (ADJUSTMENT, "Adjustment - Stock count correction"),
    ]

    product_store = models.ForeignKey(
        ProductStore, on_delete=models.CASCADE, related_name="stock_movements"
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.IntegerField(help_text="Positive for increases, negative for decreases")
    reference_number = models.CharField(
        max_length=100, blank=True, help_text="Reference number (PO, SO, Transfer ID, etc.)"
    )
    notes = models.TextField(blank=True, help_text="Additional notes about the movement")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stock_movements")

    # For transfers, track destination store
    destination_product_store = models.ForeignKey(
        ProductStore,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="incoming_transfers",
        help_text="For transfers, the destination ProductStore",
    )

    class Meta:
        db_table = "inventory_stock_movement"
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type} - {self.product_store.product.name} - {self.quantity} units"

    def clean(self):
        """Custom validation for StockMovement fields."""
        super().clean()

        # Validate quantity based on movement type
        if self.movement_type == self.INBOUND and self.quantity <= 0:
            raise ValidationError({"quantity": "Inbound movements must have positive quantity."})

        if self.movement_type == self.OUTBOUND and self.quantity >= 0:
            raise ValidationError({"quantity": "Outbound movements must have negative quantity."})

        # For transfers, validate destination
        if self.movement_type == self.TRANSFER:
            if not self.destination_product_store:
                raise ValidationError(
                    {"destination_product_store": "Transfer movements require a destination."}
                )

            # Validate different stores for transfer
            if (
                self.product_store
                and self.destination_product_store
                and self.product_store.store == self.destination_product_store.store
            ):
                raise ValidationError(
                    {"destination_product_store": "Cannot transfer to the same store."}
                )

            # Validate same product for transfer
            if (
                self.product_store
                and self.destination_product_store
                and self.product_store.product != self.destination_product_store.product
            ):
                raise ValidationError(
                    {"destination_product_store": "Transfer must be for the same product."}
                )

        # Validate user has access to the brand
        if self.created_by_id and self.product_store_id:
            user_brand = self.created_by.get_brand()
            product_brand = self.product_store.product.brand

            # System admins can access all brands
            if not self.created_by.is_system_admin() and user_brand != product_brand:
                raise ValidationError(
                    {"created_by": "User must belong to the same brand as the product."}
                )

    def save(self, *args, **kwargs):
        """Override save to run validation and update ProductStore quantity."""
        # First run validation
        self.clean()

        # Check if this record already exists in database
        is_new = self._state.adding

        if is_new:
            # Validate sufficient stock for outbound operations first
            if self.quantity < 0:  # Outbound movement
                available_stock = self.product_store.quantity_on_hand
                required_stock = abs(self.quantity)

                # Allow negative stock only for adjustments
                if available_stock < required_stock and self.movement_type != self.ADJUSTMENT:
                    raise ValidationError(
                        {
                            "quantity": f"Insufficient stock. Available: {available_stock}, Requested: {required_stock}"
                        }
                    )

            # Save the movement first
            super().save(*args, **kwargs)

            # Then update quantities
            old_quantity = self.product_store.quantity_on_hand
            new_quantity = old_quantity + self.quantity

            # Ensure non-negative stock (except for adjustments)
            if new_quantity < 0 and self.movement_type == self.ADJUSTMENT:
                self.product_store.quantity_on_hand = 0
            else:
                self.product_store.quantity_on_hand = max(0, new_quantity)

            self.product_store.save()

            # For transfers, also update destination
            if self.movement_type == self.TRANSFER and self.destination_product_store:
                dest_old_quantity = self.destination_product_store.quantity_on_hand
                self.destination_product_store.quantity_on_hand = dest_old_quantity + abs(
                    self.quantity
                )
                self.destination_product_store.save()
        else:
            # For updates, just call super without changing quantities
            super().save(*args, **kwargs)
