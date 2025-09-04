"""Tests for Product and Category models and API endpoints."""
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.roles import SYSTEM_ADMIN, BRAND_MANAGER, STORE_MANAGER, STAFF
from apps.brands.models import Brand
from .models import Category, Product

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test Category model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.brand = Brand.objects.create(name="Test Brand")
    
    def test_category_creation(self):
        """Test creating a category."""
        category = Category.objects.create(
            brand=self.brand,
            name="Electronics"
        )
        self.assertEqual(category.name, "Electronics")
        self.assertEqual(category.brand, self.brand)
        self.assertIsNone(category.parent)
        self.assertIsNotNone(category.id)
    
    def test_category_with_parent(self):
        """Test creating a category with parent."""
        parent = Category.objects.create(brand=self.brand, name="Electronics")
        child = Category.objects.create(
            brand=self.brand,
            name="Smartphones", 
            parent=parent
        )
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())
    
    def test_category_str_representation(self):
        """Test category string representation."""
        parent = Category.objects.create(brand=self.brand, name="Electronics")
        child = Category.objects.create(
            brand=self.brand,
            name="Smartphones",
            parent=parent
        )
        self.assertEqual(str(parent), "Test Brand - Electronics")
        self.assertEqual(str(child), "Test Brand - Electronics > Smartphones")
    
    def test_category_name_uniqueness_per_brand(self):
        """Test that category names are unique per brand."""
        Category.objects.create(brand=self.brand, name="Electronics")
        
        with self.assertRaises(Exception):
            category2 = Category(brand=self.brand, name="Electronics")
            category2.save()


class ProductModelTest(TestCase):
    """Test Product model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.brand = Brand.objects.create(name="Test Brand")
        self.category = Category.objects.create(brand=self.brand, name="Electronics")
    
    def test_product_creation(self):
        """Test creating a product."""
        product = Product.objects.create(
            brand=self.brand,
            sku="PROD001",
            name="Test Product",
            category=self.category
        )
        self.assertEqual(product.sku, "PROD001")
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.brand, self.brand)
        self.assertEqual(product.category, self.category)
        self.assertTrue(product.is_active)
    
    def test_product_without_category(self):
        """Test creating a product without category."""
        product = Product.objects.create(
            brand=self.brand,
            sku="PROD002",
            name="Uncategorized Product"
        )
        self.assertIsNone(product.category)
    
    def test_product_str_representation(self):
        """Test product string representation."""
        product = Product.objects.create(
            brand=self.brand,
            sku="PROD001",
            name="Test Product"
        )
        self.assertEqual(str(product), "Test Brand - Test Product (PROD001)")
    
    def test_product_sku_uniqueness_per_brand(self):
        """Test that SKUs are unique per brand."""
        Product.objects.create(
            brand=self.brand,
            sku="PROD001",
            name="Product One"
        )
        
        with self.assertRaises(Exception):
            product2 = Product(
                brand=self.brand,
                sku="PROD001",
                name="Product Two"
            )
            product2.save()
    
    def test_product_category_brand_validation(self):
        """Test that product category must belong to same brand."""
        other_brand = Brand.objects.create(name="Other Brand")
        other_category = Category.objects.create(brand=other_brand, name="Other Category")
        
        with self.assertRaises(Exception):
            product = Product(
                brand=self.brand,
                sku="PROD001",
                name="Test Product",
                category=other_category
            )
            product.save()


class CategoryAPITest(APITestCase):
    """Test Category API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create brands
        self.brand1 = Brand.objects.create(name="Brand One")
        self.brand2 = Brand.objects.create(name="Brand Two")
        
        # Create categories
        self.category1 = Category.objects.create(brand=self.brand1, name="Electronics")
        self.subcategory1 = Category.objects.create(
            brand=self.brand1,
            name="Smartphones",
            parent=self.category1
        )
        self.category2 = Category.objects.create(brand=self.brand2, name="Clothing")
        
        # Create users
        self.system_admin = User.objects.create_user(
            email="admin@test.com",
            password="TestPassword123!",
            role=SYSTEM_ADMIN,
            first_name="System",
            last_name="Admin"
        )
        
        self.brand_manager = User.objects.create_user(
            email="manager@test.com",
            password="TestPassword123!",
            role=BRAND_MANAGER,
            brand=self.brand1,
            first_name="Brand",
            last_name="Manager"
        )
        
        self.store_manager = User.objects.create_user(
            email="store@test.com",
            password="TestPassword123!",
            role=STORE_MANAGER,
            brand=self.brand1,
            first_name="Store",
            last_name="Manager"
        )
        
        self.staff = User.objects.create_user(
            email="staff@test.com",
            password="TestPassword123!",
            role=STAFF,
            brand=self.brand1,
            first_name="Staff",
            last_name="User"
        )
    
    def get_jwt_token(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_category_list_system_admin(self):
        """Test that SYSTEM_ADMIN can see all categories."""
        token = self.get_jwt_token(self.system_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_category_list_brand_scoping(self):
        """Test that non-admin users only see categories from their brand."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Electronics + Smartphones
    
    def test_category_create_brand_manager_success(self):
        """Test that BRAND_MANAGER can create categories in their brand."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'name': 'New Category'
        }
        response = self.client.post('/api/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Category')
    
    def test_category_create_with_parent(self):
        """Test creating category with parent relationship."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'name': 'Tablets',
            'parent': str(self.category1.id)
        }
        response = self.client.post('/api/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Tablets')
        self.assertEqual(str(response.data['parent']), str(self.category1.id))
    
    def test_category_create_store_manager_forbidden(self):
        """Test that STORE_MANAGER cannot create categories."""
        token = self.get_jwt_token(self.store_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'name': 'New Category'
        }
        response = self.client.post('/api/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_category_create_staff_forbidden(self):
        """Test that STAFF cannot create categories."""
        token = self.get_jwt_token(self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'name': 'New Category'
        }
        response = self.client.post('/api/categories/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_category_hierarchy_retrieval(self):
        """Test retrieving category with parent-child relationships."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get(f'/api/categories/{self.category1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['children']), 1)
        self.assertEqual(response.data['children'][0]['name'], 'Smartphones')


class ProductAPITest(APITestCase):
    """Test Product API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create brands
        self.brand1 = Brand.objects.create(name="Brand One")
        self.brand2 = Brand.objects.create(name="Brand Two")
        
        # Create categories
        self.category1 = Category.objects.create(brand=self.brand1, name="Electronics")
        self.category2 = Category.objects.create(brand=self.brand2, name="Clothing")
        
        # Create products
        self.product1 = Product.objects.create(
            brand=self.brand1,
            sku="PROD001",
            name="Smartphone",
            category=self.category1
        )
        self.product2 = Product.objects.create(
            brand=self.brand2,
            sku="PROD002",
            name="T-Shirt",
            category=self.category2
        )
        
        # Create users
        self.system_admin = User.objects.create_user(
            email="admin@test.com",
            password="TestPassword123!",
            role=SYSTEM_ADMIN,
            first_name="System",
            last_name="Admin"
        )
        
        self.brand_manager = User.objects.create_user(
            email="manager@test.com",
            password="TestPassword123!",
            role=BRAND_MANAGER,
            brand=self.brand1,
            first_name="Brand",
            last_name="Manager"
        )
        
        self.store_manager = User.objects.create_user(
            email="store@test.com",
            password="TestPassword123!",
            role=STORE_MANAGER,
            brand=self.brand1,
            first_name="Store",
            last_name="Manager"
        )
        
        self.staff = User.objects.create_user(
            email="staff@test.com",
            password="TestPassword123!",
            role=STAFF,
            brand=self.brand1,
            first_name="Staff",
            last_name="User"
        )
    
    def get_jwt_token(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_product_list_system_admin(self):
        """Test that SYSTEM_ADMIN can see all products."""
        token = self.get_jwt_token(self.system_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_product_list_brand_scoping(self):
        """Test that non-admin users only see products from their brand."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Smartphone')
    
    def test_product_create_brand_manager_success(self):
        """Test that BRAND_MANAGER can create products in their brand."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'sku': 'PROD003',
            'name': 'New Product',
            'category': str(self.category1.id),
            'is_active': True
        }
        response = self.client.post('/api/products/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Product')
    
    def test_product_create_store_manager_forbidden(self):
        """Test that STORE_MANAGER cannot create products."""
        token = self.get_jwt_token(self.store_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'sku': 'PROD003',
            'name': 'New Product',
            'is_active': True
        }
        response = self.client.post('/api/products/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_product_create_staff_forbidden(self):
        """Test that STAFF cannot create products."""
        token = self.get_jwt_token(self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'sku': 'PROD003',
            'name': 'New Product',
            'is_active': True
        }
        response = self.client.post('/api/products/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_product_is_active_filtering(self):
        """Test is_active filtering functionality."""
        # Create inactive product
        inactive_product = Product.objects.create(
            brand=self.brand1,
            sku="PROD_INACTIVE",
            name="Inactive Product",
            is_active=False
        )
        
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Test without filter - should return all products for the brand
        response = self.client.get('/api/products/')
        self.assertEqual(len(response.data['results']), 2)
        
        # Test with is_active=true filter
        response = self.client.get('/api/products/?is_active=true')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Smartphone')
        
        # Test with is_active=false filter
        response = self.client.get('/api/products/?is_active=false')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Inactive Product')
    
    def test_product_isolation(self):
        """Test that users cannot access products from other brands."""
        brand2_manager = User.objects.create_user(
            email="manager2@test.com",
            password="TestPassword123!",
            role=BRAND_MANAGER,
            brand=self.brand2,
            first_name="Brand2",
            last_name="Manager"
        )
        
        token = self.get_jwt_token(brand2_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'T-Shirt')
