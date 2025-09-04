"""Tests for user authentication and management."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.roles import SYSTEM_ADMIN, STAFF

User = get_user_model()


class AuthenticationTestCase(APITestCase):
    """Test cases for authentication endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.login_url = reverse('accounts:token_obtain_pair')
        self.refresh_url = reverse('accounts:token_refresh')
        self.logout_url = reverse('accounts:logout')
        self.me_url = reverse('accounts:user_me')
        self.users_url = reverse('accounts:user_list')
        
        # Create test users
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User'
        )
        
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='StaffPass123!',
            first_name='Staff',
            last_name='Member',
            role=STAFF
        )
        
        # Create soft-deleted user
        self.deleted_user = User.objects.create_user(
            email='deleted@test.com',
            password='DeletedPass123!',
            first_name='Deleted',
            last_name='User',
            role=STAFF
        )
        self.deleted_user.soft_delete()
    
    def test_successful_login(self):
        """Test successful login returns tokens and user data."""
        data = {
            'email': 'admin@test.com',
            'password': 'AdminPass123!'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'admin@test.com')
        self.assertEqual(response.data['user']['role'], SYSTEM_ADMIN)
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials fails."""
        data = {
            'email': 'admin@test.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_deleted_user_login_blocked(self):
        """Test that soft-deleted users cannot login."""
        data = {
            'email': 'deleted@test.com',
            'password': 'DeletedPass123!'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ACCOUNT_DELETED', str(response.data))
    
    def test_refresh_token_rotation(self):
        """Test that refresh token rotation works correctly."""
        # Login to get initial tokens
        login_data = {
            'email': 'admin@test.com',
            'password': 'AdminPass123!'
        }
        login_response = self.client.post(self.login_url, login_data)
        initial_refresh = login_response.data['refresh']
        
        # Use refresh token to get new tokens
        refresh_data = {'refresh': initial_refresh}
        refresh_response = self.client.post(self.refresh_url, refresh_data)
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        self.assertIn('refresh', refresh_response.data)
        
        # New refresh token should be different from initial
        new_refresh = refresh_response.data['refresh']
        self.assertNotEqual(initial_refresh, new_refresh)
        
        # Initial refresh token should be blacklisted (can't use again)
        old_refresh_response = self.client.post(self.refresh_url, {'refresh': initial_refresh})
        self.assertEqual(old_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_blacklists_token(self):
        """Test that logout properly blacklists refresh token."""
        # Login
        login_data = {
            'email': 'admin@test.com',
            'password': 'AdminPass123!'
        }
        login_response = self.client.post(self.login_url, login_data)
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']
        
        # Logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_response = self.client.post(self.logout_url, {'refresh': refresh_token})
        
        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)
        
        # Try to use blacklisted refresh token
        refresh_response = self.client.post(self.refresh_url, {'refresh': refresh_token})
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserManagementTestCase(APITestCase):
    """Test cases for user management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.me_url = reverse('accounts:user_me')
        self.users_url = reverse('accounts:user_list')
        
        # Create test users
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User'
        )
        
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='StaffPass123!',
            first_name='Staff',
            last_name='Member',
            role=STAFF
        )
    
    def test_user_me_endpoint_authenticated(self):
        """Test authenticated user can access their profile."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'admin@test.com')
        self.assertEqual(response.data['role'], SYSTEM_ADMIN)
        self.assertEqual(response.data['full_name'], 'Admin User')
    
    def test_user_me_endpoint_unauthenticated(self):
        """Test unauthenticated user cannot access profile endpoint."""
        response = self.client.get(self.me_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_admin_can_list_users(self):
        """Test system admin can list all users."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # admin and staff user
    
    def test_staff_cannot_list_users(self):
        """Test staff user cannot list users."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_unauthenticated_cannot_list_users(self):
        """Test unauthenticated user cannot list users."""
        response = self.client.get(self.users_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordValidationTestCase(APITestCase):
    """Test cases for custom password validation."""
    
    def test_weak_password_rejected(self):
        """Test that weak passwords are rejected."""
        from django.core.exceptions import ValidationError
        from django.contrib.auth.password_validation import validate_password
        from apps.accounts.validators import ComplexPasswordValidator
        
        validator = ComplexPasswordValidator()
        
        # Test short password
        with self.assertRaises(ValidationError):
            validator.validate('short')
        
        # Test password without uppercase
        with self.assertRaises(ValidationError):
            validator.validate('lowercase123!')
        
        # Test password without lowercase
        with self.assertRaises(ValidationError):
            validator.validate('UPPERCASE123!')
        
        # Test password without digit
        with self.assertRaises(ValidationError):
            validator.validate('NoDigitPass!')
        
        # Test password without symbol
        with self.assertRaises(ValidationError):
            validator.validate('NoSymbol123')
    
    def test_strong_password_accepted(self):
        """Test that strong passwords are accepted."""
        from apps.accounts.validators import ComplexPasswordValidator
        
        validator = ComplexPasswordValidator()
        
        # This should not raise any exception
        try:
            validator.validate('StrongPass123!')
        except Exception as e:
            self.fail(f"Strong password was rejected: {e}")
        
        # Also test with user creation
        user = User.objects.create_user(
            email='test@test.com',
            password='StrongPass123!',
            first_name='Test',
            last_name='User'
        )
        
        self.assertEqual(user.email, 'test@test.com')
        self.assertTrue(user.check_password('StrongPass123!'))


class UserModelTestCase(APITestCase):
    """Test cases for User model functionality."""
    
    def test_user_creation_with_uuid(self):
        """Test user is created with UUID primary key."""
        user = User.objects.create_user(
            email='test@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        # Check UUID format
        self.assertEqual(len(str(user.id)), 36)  # UUID string length
        self.assertIn('-', str(user.id))  # UUID has hyphens
    
    def test_soft_delete_functionality(self):
        """Test soft delete methods work correctly."""
        user = User.objects.create_user(
            email='test@test.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )
        
        # User should be in normal queryset
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.unfiltered().count(), 1)
        
        # Soft delete the user
        user.soft_delete()
        
        # User should be hidden from normal queryset but visible in unfiltered
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(User.objects.unfiltered().count(), 1)
        self.assertTrue(user.is_deleted)
        self.assertIsNotNone(user.deleted_at)
        
        # Restore the user
        user.restore()
        
        # User should be back in normal queryset
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(user.is_deleted)
        self.assertIsNone(user.deleted_at)
    
    def test_user_role_methods(self):
        """Test user role helper methods."""
        admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='AdminPass123!',
            first_name='Admin',
            last_name='User'
        )
        
        staff_user = User.objects.create_user(
            email='staff@test.com',
            password='StaffPass123!',
            first_name='Staff',
            last_name='User',
            role=STAFF
        )
        
        # Test role checking methods
        self.assertTrue(admin_user.has_role(SYSTEM_ADMIN))
        self.assertFalse(admin_user.has_role(STAFF))
        self.assertTrue(admin_user.is_system_admin())
        
        self.assertTrue(staff_user.has_role(STAFF))
        self.assertFalse(staff_user.has_role(SYSTEM_ADMIN))
        self.assertFalse(staff_user.is_system_admin())
