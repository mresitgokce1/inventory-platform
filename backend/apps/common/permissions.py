"""Common permission decorators and utilities."""

from functools import wraps
from django.http import JsonResponse
from django.contrib.auth import get_user_model

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