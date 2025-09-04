"""Tests for Store models and API endpoints."""
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.roles import SYSTEM_ADMIN, BRAND_MANAGER, STORE_MANAGER, STAFF
from apps.brands.models import Brand
from .models import Store

User = get_user_model()


class StoreModelTest(TestCase):
    """Test Store model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.brand = Brand.objects.create(name="Test Brand")
    
    def test_store_creation(self):
        """Test creating a store."""
        store = Store.objects.create(
            brand=self.brand,
            name="Test Store",
            code="TS001"
        )
        self.assertEqual(store.name, "Test Store")
        self.assertEqual(store.code, "TS001")
        self.assertEqual(store.brand, self.brand)
        self.assertTrue(store.is_active)
        self.assertIsNotNone(store.id)
    
    def test_store_str_representation(self):
        """Test store string representation."""
        store = Store.objects.create(
            brand=self.brand,
            name="Test Store",
            code="TS001"
        )
        self.assertEqual(str(store), "Test Brand - Test Store")
    
    def test_store_name_uniqueness_per_brand(self):
        """Test that store names are unique per brand."""
        Store.objects.create(brand=self.brand, name="Test Store", code="TS001")
        
        with self.assertRaises(Exception):
            store2 = Store(brand=self.brand, name="Test Store", code="TS002")
            store2.save()
    
    def test_store_code_uniqueness_per_brand(self):
        """Test that store codes are unique per brand."""
        Store.objects.create(brand=self.brand, name="Store One", code="TS001")
        
        with self.assertRaises(Exception):
            store2 = Store(brand=self.brand, name="Store Two", code="TS001")
            store2.save()
    
    def test_store_name_case_insensitive_uniqueness(self):
        """Test that store names are unique case-insensitive per brand."""
        Store.objects.create(brand=self.brand, name="Test Store", code="TS001")
        
        with self.assertRaises(Exception):
            store2 = Store(brand=self.brand, name="TEST STORE", code="TS002")
            store2.save()


class StoreAPITest(APITestCase):
    """Test Store API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create brands
        self.brand1 = Brand.objects.create(name="Brand One")
        self.brand2 = Brand.objects.create(name="Brand Two")
        
        # Create stores
        self.store1 = Store.objects.create(
            brand=self.brand1,
            name="Store One",
            code="S001"
        )
        self.store2 = Store.objects.create(
            brand=self.brand2,
            name="Store Two",
            code="S002"
        )
        
        # Create users with different roles
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
    
    def test_store_list_system_admin(self):
        """Test that SYSTEM_ADMIN can see all stores."""
        token = self.get_jwt_token(self.system_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/stores/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_store_list_brand_scoping(self):
        """Test that non-admin users only see stores from their brand."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/stores/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Store One')
    
    def test_store_create_brand_manager_success(self):
        """Test that BRAND_MANAGER can create stores in their brand."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'name': 'New Store',
            'code': 'NS001',
            'is_active': True
        }
        response = self.client.post('/api/stores/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Store')
    
    def test_store_create_brand_manager_wrong_brand_forbidden(self):
        """Test that BRAND_MANAGER cannot create stores in other brands."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand2.id),
            'name': 'New Store',
            'code': 'NS001',
            'is_active': True
        }
        response = self.client.post('/api/stores/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_store_create_store_manager_forbidden(self):
        """Test that STORE_MANAGER cannot create stores."""
        token = self.get_jwt_token(self.store_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'name': 'New Store',
            'code': 'NS001',
            'is_active': True
        }
        response = self.client.post('/api/stores/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_store_create_staff_forbidden(self):
        """Test that STAFF cannot create stores."""
        token = self.get_jwt_token(self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'name': 'New Store',
            'code': 'NS001',
            'is_active': True
        }
        response = self.client.post('/api/stores/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_store_update_store_manager_success(self):
        """Test that STORE_MANAGER can update stores."""
        token = self.get_jwt_token(self.store_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'name': 'Updated Store',
            'code': 'S001',
            'is_active': False
        }
        response = self.client.put(f'/api/stores/{self.store1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Store')
    
    def test_store_update_staff_forbidden(self):
        """Test that STAFF cannot update stores."""
        token = self.get_jwt_token(self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'brand': str(self.brand1.id),
            'name': 'Updated Store',
            'code': 'S001',
            'is_active': False
        }
        response = self.client.put(f'/api/stores/{self.store1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_store_isolation(self):
        """Test that users cannot access stores from other brands."""
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
        
        response = self.client.get('/api/stores/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Store Two')
    
    def test_store_is_active_filtering(self):
        """Test is_active filtering functionality."""
        # Create inactive store
        inactive_store = Store.objects.create(
            brand=self.brand1,
            name="Inactive Store",
            code="IS001",
            is_active=False
        )
        
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Test without filter - should return all stores for the brand
        response = self.client.get('/api/stores/')
        self.assertEqual(len(response.data['results']), 2)
        
        # Test with is_active=true filter
        response = self.client.get('/api/stores/?is_active=true')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Store One')
        
        # Test with is_active=false filter
        response = self.client.get('/api/stores/?is_active=false')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Inactive Store')
