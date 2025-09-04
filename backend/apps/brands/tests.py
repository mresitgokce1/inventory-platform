"""Tests for Brand models and API endpoints."""
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.roles import SYSTEM_ADMIN, BRAND_MANAGER, STORE_MANAGER, STAFF
from .models import Brand

User = get_user_model()


class BrandModelTest(TestCase):
    """Test Brand model functionality."""
    
    def test_brand_creation(self):
        """Test creating a brand."""
        brand = Brand.objects.create(name="Test Brand")
        self.assertEqual(brand.name, "Test Brand")
        self.assertTrue(brand.is_active)
        self.assertIsNotNone(brand.id)
        self.assertIsNotNone(brand.created_at)
        self.assertIsNotNone(brand.updated_at)
    
    def test_brand_str_representation(self):
        """Test brand string representation."""
        brand = Brand.objects.create(name="Test Brand")
        self.assertEqual(str(brand), "Test Brand")
    
    def test_brand_name_uniqueness_case_insensitive(self):
        """Test that brand names are unique case-insensitive."""
        Brand.objects.create(name="Test Brand")
        
        with self.assertRaises(Exception):
            brand2 = Brand(name="TEST BRAND")
            brand2.save()
    
    def test_brand_is_active_default(self):
        """Test that brands are active by default."""
        brand = Brand.objects.create(name="Test Brand")
        self.assertTrue(brand.is_active)


class BrandAPITest(APITestCase):
    """Test Brand API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create brands
        self.brand1 = Brand.objects.create(name="Brand One")
        self.brand2 = Brand.objects.create(name="Brand Two")
        
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
    
    def test_brand_list_system_admin(self):
        """Test that SYSTEM_ADMIN can see all brands."""
        token = self.get_jwt_token(self.system_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/brands/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_brand_list_brand_manager(self):
        """Test that BRAND_MANAGER can only see their own brand."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/brands/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Brand One')
    
    def test_brand_create_system_admin_success(self):
        """Test that SYSTEM_ADMIN can create brands."""
        token = self.get_jwt_token(self.system_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'name': 'New Brand', 'is_active': True}
        response = self.client.post('/api/brands/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Brand')
    
    def test_brand_create_brand_manager_forbidden(self):
        """Test that BRAND_MANAGER cannot create brands."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'name': 'New Brand', 'is_active': True}
        response = self.client.post('/api/brands/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_brand_create_store_manager_forbidden(self):
        """Test that STORE_MANAGER cannot create brands."""
        token = self.get_jwt_token(self.store_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'name': 'New Brand', 'is_active': True}
        response = self.client.post('/api/brands/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_brand_create_staff_forbidden(self):
        """Test that STAFF cannot create brands."""
        token = self.get_jwt_token(self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'name': 'New Brand', 'is_active': True}
        response = self.client.post('/api/brands/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_brand_update_system_admin_success(self):
        """Test that SYSTEM_ADMIN can update brands."""
        token = self.get_jwt_token(self.system_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'name': 'Updated Brand', 'is_active': False}
        response = self.client.put(f'/api/brands/{self.brand1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Brand')
        self.assertFalse(response.data['is_active'])
    
    def test_brand_update_brand_manager_forbidden(self):
        """Test that BRAND_MANAGER cannot update brands."""
        token = self.get_jwt_token(self.brand_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'name': 'Updated Brand', 'is_active': False}
        response = self.client.put(f'/api/brands/{self.brand1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_brand_isolation(self):
        """Test that users from one brand cannot see another brand's data."""
        # Create another brand manager for brand2
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
        
        response = self.client.get('/api/brands/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Brand Two')
    
    def test_brand_is_active_filtering(self):
        """Test is_active filtering functionality."""
        # Create inactive brand
        inactive_brand = Brand.objects.create(name="Inactive Brand", is_active=False)
        
        token = self.get_jwt_token(self.system_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Test without filter - should return all brands
        response = self.client.get('/api/brands/')
        self.assertEqual(len(response.data['results']), 3)
        
        # Test with is_active=true filter
        response = self.client.get('/api/brands/?is_active=true')
        self.assertEqual(len(response.data['results']), 2)
        
        # Test with is_active=false filter
        response = self.client.get('/api/brands/?is_active=false')
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Inactive Brand')
    
    def test_brand_create_duplicate_name_case_insensitive(self):
        """Test that creating brand with duplicate name (case-insensitive) fails."""
        token = self.get_jwt_token(self.system_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {'name': 'BRAND ONE', 'is_active': True}
        response = self.client.post('/api/brands/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
