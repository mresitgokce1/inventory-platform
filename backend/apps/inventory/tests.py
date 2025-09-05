"""Tests for Inventory models and API endpoints."""

import json

from apps.accounts.roles import BRAND_MANAGER, STAFF, STORE_MANAGER, SYSTEM_ADMIN
from apps.brands.models import Brand
from apps.products.models import Category, Product
from apps.stores.models import Store
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ProductStore, StockMovement

User = get_user_model()


class ProductStoreModelTest(TestCase):
    """Test ProductStore model functionality."""

    def setUp(self):
        """Set up test data."""
        self.brand = Brand.objects.create(name="Test Brand")
        self.store = Store.objects.create(brand=self.brand, name="Test Store", code="TS001")
        self.category = Category.objects.create(brand=self.brand, name="Test Category")
        self.product = Product.objects.create(
            brand=self.brand, sku="TEST001", name="Test Product", category=self.category
        )

    def test_product_store_creation(self):
        """Test creating a ProductStore."""
        product_store = ProductStore.objects.create(
            product=self.product,
            store=self.store,
            quantity_on_hand=100,
            reserved_quantity=10,
            minimum_stock_level=5,
        )

        self.assertEqual(product_store.product, self.product)
        self.assertEqual(product_store.store, self.store)
        self.assertEqual(product_store.quantity_on_hand, 100)
        self.assertEqual(product_store.reserved_quantity, 10)
        self.assertEqual(product_store.minimum_stock_level, 5)
        self.assertIsNotNone(product_store.id)

    def test_product_store_str_representation(self):
        """Test ProductStore string representation."""
        product_store = ProductStore.objects.create(
            product=self.product, store=self.store, quantity_on_hand=100
        )
        expected = f"{self.product.name} @ {self.store.name} - 100 units"
        self.assertEqual(str(product_store), expected)

    def test_available_quantity_property(self):
        """Test available_quantity property calculation."""
        product_store = ProductStore.objects.create(
            product=self.product, store=self.store, quantity_on_hand=100, reserved_quantity=20
        )
        self.assertEqual(product_store.available_quantity, 80)

        # Test negative case
        product_store.reserved_quantity = 120
        self.assertEqual(product_store.available_quantity, 0)

    def test_is_below_minimum_property(self):
        """Test is_below_minimum property."""
        product_store = ProductStore.objects.create(
            product=self.product, store=self.store, quantity_on_hand=10, minimum_stock_level=15
        )
        self.assertTrue(product_store.is_below_minimum)

        product_store.quantity_on_hand = 20
        self.assertFalse(product_store.is_below_minimum)

    def test_product_store_unique_constraint(self):
        """Test unique constraint for product-store combination."""
        ProductStore.objects.create(product=self.product, store=self.store, quantity_on_hand=100)

        # Creating another ProductStore with same product-store should fail
        with self.assertRaises(Exception):  # IntegrityError
            ProductStore.objects.create(product=self.product, store=self.store, quantity_on_hand=50)

    def test_brand_validation(self):
        """Test that product and store must belong to same brand."""
        other_brand = Brand.objects.create(name="Other Brand")
        other_store = Store.objects.create(brand=other_brand, name="Other Store", code="OS001")

        product_store = ProductStore(
            product=self.product,  # belongs to self.brand
            store=other_store,  # belongs to other_brand
            quantity_on_hand=100,
        )

        with self.assertRaises(ValidationError) as context:
            product_store.clean()

        self.assertIn("product", context.exception.message_dict)

    def test_reserved_quantity_validation(self):
        """Test that reserved quantity cannot exceed on hand quantity."""
        product_store = ProductStore(
            product=self.product,
            store=self.store,
            quantity_on_hand=50,
            reserved_quantity=60,  # More than on hand
        )

        with self.assertRaises(ValidationError) as context:
            product_store.clean()

        self.assertIn("reserved_quantity", context.exception.message_dict)


class StockMovementModelTest(TestCase):
    """Test StockMovement model functionality."""

    def setUp(self):
        """Set up test data."""
        self.brand = Brand.objects.create(name="Test Brand")
        self.store1 = Store.objects.create(brand=self.brand, name="Store 1", code="S001")
        self.store2 = Store.objects.create(brand=self.brand, name="Store 2", code="S002")
        self.category = Category.objects.create(brand=self.brand, name="Test Category")
        self.product = Product.objects.create(
            brand=self.brand, sku="TEST001", name="Test Product", category=self.category
        )
        self.product_store1 = ProductStore.objects.create(
            product=self.product, store=self.store1, quantity_on_hand=100
        )
        self.product_store2 = ProductStore.objects.create(
            product=self.product, store=self.store2, quantity_on_hand=50
        )
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", role=BRAND_MANAGER, brand=self.brand
        )

    def test_stock_movement_creation(self):
        """Test creating a StockMovement."""
        movement = StockMovement.objects.create(
            product_store=self.product_store1,
            movement_type=StockMovement.INBOUND,
            quantity=50,
            reference_number="PO001",
            notes="Initial stock",
            created_by=self.user,
        )

        self.assertEqual(movement.product_store, self.product_store1)
        self.assertEqual(movement.movement_type, StockMovement.INBOUND)
        self.assertEqual(movement.quantity, 50)
        self.assertEqual(movement.reference_number, "PO001")
        self.assertEqual(movement.created_by, self.user)
        self.assertIsNotNone(movement.id)

    def test_stock_movement_str_representation(self):
        """Test StockMovement string representation."""
        movement = StockMovement.objects.create(
            product_store=self.product_store1,
            movement_type=StockMovement.INBOUND,
            quantity=50,
            created_by=self.user,
        )
        expected = f"INBOUND - {self.product.name} - 50 units"
        self.assertEqual(str(movement), expected)

    def test_inbound_movement_validation(self):
        """Test validation for inbound movements."""
        # Inbound movements must have positive quantity
        movement = StockMovement(
            product_store=self.product_store1,
            movement_type=StockMovement.INBOUND,
            quantity=-10,  # Should be positive
            created_by=self.user,
        )

        with self.assertRaises(ValidationError) as context:
            movement.clean()

        self.assertIn("quantity", context.exception.message_dict)

    def test_outbound_movement_validation(self):
        """Test validation for outbound movements."""
        # Outbound movements must have negative quantity
        movement = StockMovement(
            product_store=self.product_store1,
            movement_type=StockMovement.OUTBOUND,
            quantity=10,  # Should be negative
            created_by=self.user,
        )

        with self.assertRaises(ValidationError) as context:
            movement.clean()

        self.assertIn("quantity", context.exception.message_dict)

    def test_transfer_movement_validation(self):
        """Test validation for transfer movements."""
        # Transfer movements require destination
        movement = StockMovement(
            product_store=self.product_store1,
            movement_type=StockMovement.TRANSFER,
            quantity=-10,
            created_by=self.user,
            # Missing destination_product_store
        )

        with self.assertRaises(ValidationError) as context:
            movement.clean()

        self.assertIn("destination_product_store", context.exception.message_dict)

    def test_transfer_same_store_validation(self):
        """Test that transfers cannot be to the same store."""
        movement = StockMovement(
            product_store=self.product_store1,
            movement_type=StockMovement.TRANSFER,
            quantity=-10,
            destination_product_store=self.product_store1,  # Same store
            created_by=self.user,
        )

        with self.assertRaises(ValidationError) as context:
            movement.clean()

        self.assertIn("destination_product_store", context.exception.message_dict)

    def test_stock_movement_updates_quantity(self):
        """Test that stock movements update ProductStore quantity."""
        initial_quantity = self.product_store1.quantity_on_hand

        # Create inbound movement
        StockMovement.objects.create(
            product_store=self.product_store1,
            movement_type=StockMovement.INBOUND,
            quantity=25,
            created_by=self.user,
        )

        # Refresh from database
        self.product_store1.refresh_from_db()
        self.assertEqual(self.product_store1.quantity_on_hand, initial_quantity + 25)

    def test_insufficient_stock_validation(self):
        """Test that movements don't create negative stock."""
        # Try to create outbound movement larger than available stock
        with self.assertRaises(ValidationError):
            StockMovement.objects.create(
                product_store=self.product_store1,
                movement_type=StockMovement.OUTBOUND,
                quantity=-200,  # More than available (100)
                created_by=self.user,
            )

    def test_brand_access_validation(self):
        """Test that users can only create movements for their brand."""
        other_brand = Brand.objects.create(name="Other Brand")
        other_user = User.objects.create_user(
            email="other@example.com", password="testpass123", role=BRAND_MANAGER, brand=other_brand
        )

        movement = StockMovement(
            product_store=self.product_store1,  # belongs to self.brand
            movement_type=StockMovement.INBOUND,
            quantity=10,
            created_by=other_user,  # belongs to other_brand
        )

        with self.assertRaises(ValidationError) as context:
            movement.clean()

        self.assertIn("created_by", context.exception.message_dict)


class InventoryAPITest(APITestCase):
    """Test Inventory API endpoints."""

    def setUp(self):
        """Set up test data."""
        # Create brands
        self.brand1 = Brand.objects.create(name="Brand One")
        self.brand2 = Brand.objects.create(name="Brand Two")

        # Create stores
        self.store1 = Store.objects.create(brand=self.brand1, name="Store 1", code="S001")
        self.store2 = Store.objects.create(brand=self.brand1, name="Store 2", code="S002")

        # Create categories and products
        self.category = Category.objects.create(brand=self.brand1, name="Category 1")
        self.product1 = Product.objects.create(
            brand=self.brand1, sku="PROD001", name="Product 1", category=self.category
        )
        self.product2 = Product.objects.create(
            brand=self.brand1, sku="PROD002", name="Product 2", category=self.category
        )

        # Create ProductStore records
        self.product_store1 = ProductStore.objects.create(
            product=self.product1, store=self.store1, quantity_on_hand=100, minimum_stock_level=10
        )
        self.product_store2 = ProductStore.objects.create(
            product=self.product2, store=self.store1, quantity_on_hand=5, minimum_stock_level=10
        )

        # Create users with different roles
        self.system_admin = User.objects.create_user(
            email="admin@test.com", password="TestPassword123!", role=SYSTEM_ADMIN
        )
        self.brand_manager = User.objects.create_user(
            email="manager@test.com",
            password="TestPassword123!",
            role=BRAND_MANAGER,
            brand=self.brand1,
        )
        self.store_manager = User.objects.create_user(
            email="store@test.com",
            password="TestPassword123!",
            role=STORE_MANAGER,
            brand=self.brand1,
        )
        self.staff = User.objects.create_user(
            email="staff@test.com", password="TestPassword123!", role=STAFF, brand=self.brand1
        )

    def get_jwt_token(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_product_store_list_system_admin(self):
        """Test that SYSTEM_ADMIN can see all product stores."""
        token = self.get_jwt_token(self.system_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get("/api/product-stores/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_product_store_list_brand_manager(self):
        """Test that BRAND_MANAGER can see their brand's product stores."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get("/api/product-stores/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_product_store_create_brand_manager_success(self):
        """Test that BRAND_MANAGER can create product stores."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        data = {
            "product": self.product2.id,
            "store": self.store2.id,
            "quantity_on_hand": 50,
            "minimum_stock_level": 5,
        }

        response = self.client.post("/api/product-stores/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_product_store_create_staff_forbidden(self):
        """Test that STAFF cannot create product stores."""
        token = self.get_jwt_token(self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        data = {"product": self.product2.id, "store": self.store2.id, "quantity_on_hand": 50}

        response = self.client.post("/api/product-stores/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_stock_movement_create_inbound(self):
        """Test creating inbound stock movement."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        data = {
            "product_store": self.product_store1.id,
            "movement_type": "INBOUND",
            "quantity": 50,
            "reference_number": "PO001",
            "notes": "Restocking",
        }

        response = self.client.post("/api/stock-movements/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that quantity was updated
        self.product_store1.refresh_from_db()
        self.assertEqual(self.product_store1.quantity_on_hand, 150)

    def test_stock_movement_create_outbound(self):
        """Test creating outbound stock movement."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        data = {
            "product_store": self.product_store1.id,
            "movement_type": "OUTBOUND",
            "quantity": -20,
            "reference_number": "SO001",
            "notes": "Sale",
        }

        response = self.client.post("/api/stock-movements/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that quantity was updated
        self.product_store1.refresh_from_db()
        self.assertEqual(self.product_store1.quantity_on_hand, 80)

    def test_low_stock_endpoint(self):
        """Test low stock endpoint."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get("/api/product-stores/low_stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should return product_store2 which has quantity (5) below minimum (10)
        # Check if response is paginated
        if "results" in response.data:
            results = response.data["results"]
        else:
            results = response.data

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.product_store2.id))

    def test_stock_movement_immutable(self):
        """Test that stock movements cannot be updated."""
        # First create a movement
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        data = {"product_store": self.product_store1.id, "movement_type": "INBOUND", "quantity": 10}

        response = self.client.post("/api/stock-movements/", data)
        movement_id = response.data["id"]

        # Try to update it
        update_data = {"quantity": 20}
        response = self.client.patch(f"/api/stock-movements/{movement_id}/", update_data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_brand_isolation(self):
        """Test that users can only see their brand's data."""
        # Create user from different brand
        other_brand_user = User.objects.create_user(
            email="other@test.com",
            password="TestPassword123!",
            role=BRAND_MANAGER,
            brand=self.brand2,
        )

        token = self.get_jwt_token(other_brand_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get("/api/product-stores/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)  # Should see no data from brand1
