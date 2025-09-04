"""Brand views for the inventory platform."""
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Q
from apps.common.permissions import BrandScopedPermission
from apps.accounts.roles import SYSTEM_ADMIN
from .models import Brand
from .serializers import BrandSerializer


class BrandViewSet(viewsets.ModelViewSet):
    """ViewSet for Brand model with role-based permissions."""
    
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [BrandScopedPermission]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Apply is_active filter if requested
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(is_active=False)
        
        # System admins see all brands
        if user.is_system_admin():
            return queryset
        
        # Non-admin users only see their own brand
        user_brand = user.get_brand()
        if user_brand:
            return queryset.filter(id=user_brand.id)
        
        # Users without brand see nothing
        return queryset.none()
    
    def create(self, request, *args, **kwargs):
        """Only SYSTEM_ADMIN can create brands."""
        if not request.user.is_system_admin():
            return Response(
                {"detail": "forbidden", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Handle brand updates with proper permissions."""
        if not request.user.is_system_admin():
            return Response(
                {"detail": "forbidden", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Handle brand deletion with proper permissions."""
        if not request.user.is_system_admin():
            return Response(
                {"detail": "forbidden", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
