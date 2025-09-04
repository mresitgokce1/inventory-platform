"""Common permission decorators and utilities."""

from functools import wraps
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework import permissions
from apps.accounts.roles import SYSTEM_ADMIN, BRAND_MANAGER, STORE_MANAGER, STAFF

User = get_user_model()


def require_roles(*allowed_roles):
    """
    Decorator that restricts access to users with specific roles.
    Returns 403 JSON response for unauthorized access.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return JsonResponse(
                    {"detail": "forbidden", "code": "PERMISSION_DENIED"}, 
                    status=403
                )
            
            # Check if user has required role
            if not request.user.has_role(*allowed_roles):
                return JsonResponse(
                    {"detail": "forbidden", "code": "PERMISSION_DENIED"}, 
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


class RequireRolesMixin:
    """
    Mixin for class-based views to require specific roles.
    """
    required_roles = None
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse(
                {"detail": "forbidden", "code": "PERMISSION_DENIED"}, 
                status=403
            )
        
        # Check if user has required role
        if self.required_roles and not request.user.has_role(*self.required_roles):
            return JsonResponse(
                {"detail": "forbidden", "code": "PERMISSION_DENIED"}, 
                status=403
            )
        
        return super().dispatch(request, *args, **kwargs)


class BrandPermission(permissions.BasePermission):
    """
    Custom permission class for brand-based access control.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if not request.user.is_authenticated:
            return False
        
        # System admins have full access
        if request.user.is_system_admin():
            return True
        
        # For non-admin users, check role-specific permissions
        if hasattr(view, 'get_required_permissions'):
            required_permissions = view.get_required_permissions(request.method)
            return request.user.has_role(*required_permissions)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object."""
        if not request.user.is_authenticated:
            return False
        
        # System admins have full access
        if request.user.is_system_admin():
            return True
        
        # Check if object belongs to user's brand
        user_brand = request.user.get_brand()
        if not user_brand:
            return False
        
        # Get object's brand
        obj_brand = None
        if hasattr(obj, 'brand'):
            obj_brand = obj.brand
        elif hasattr(obj, 'brand_id'):
            obj_brand = obj.brand
        elif obj.__class__.__name__ == 'Brand':
            obj_brand = obj
        
        return obj_brand == user_brand


class BrandScopedPermission(permissions.BasePermission):
    """
    Permission class that enforces brand scoping for non-admin users.
    """
    
    # Role-based permissions matrix
    ROLE_PERMISSIONS = {
        SYSTEM_ADMIN: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        BRAND_MANAGER: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        STORE_MANAGER: ['GET', 'PUT', 'PATCH'],  # Can only read and update, not create/delete
        STAFF: ['GET'],  # Read-only
    }
    
    # Model-specific permission overrides
    MODEL_PERMISSIONS = {
        'Brand': {
            SYSTEM_ADMIN: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
            BRAND_MANAGER: ['GET'],  # Cannot create/modify brands
            STORE_MANAGER: ['GET'],
            STAFF: ['GET'],
        },
        'Store': {
            STORE_MANAGER: ['GET', 'PUT', 'PATCH'],  # Can manage their own stores
        }
    }
    
    def has_permission(self, request, view):
        """Check if user has permission for the action."""
        if not request.user.is_authenticated:
            return False
        
        # Get model name
        model_name = getattr(view, 'queryset', None)
        if model_name:
            model_name = model_name.model.__name__
        
        # Get permissions for user role and model
        role_permissions = self.ROLE_PERMISSIONS.get(request.user.role, [])
        model_permissions = self.MODEL_PERMISSIONS.get(model_name, {})
        final_permissions = model_permissions.get(request.user.role, role_permissions)
        
        return request.method in final_permissions
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object."""
        if not request.user.is_authenticated:
            return False
        
        # System admins have full access
        if request.user.is_system_admin():
            return True
        
        # Check brand scoping for non-admin users
        user_brand = request.user.get_brand()
        if not user_brand:
            return False
        
        # Get object's brand
        obj_brand = None
        if hasattr(obj, 'brand'):
            obj_brand = obj.brand
        elif obj.__class__.__name__ == 'Brand':
            obj_brand = obj
        
        return obj_brand == user_brand