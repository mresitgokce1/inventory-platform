"""Store views for the inventory platform."""
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Q
from apps.common.permissions import BrandScopedPermission
from apps.accounts.roles import SYSTEM_ADMIN, BRAND_MANAGER, STORE_MANAGER, STAFF
from .models import Store
from .serializers import StoreSerializer, StoreDetailSerializer


class StoreViewSet(viewsets.ModelViewSet):
    """ViewSet for Store model with role-based permissions."""
    
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [BrandScopedPermission]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return StoreDetailSerializer
        return StoreSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions and brand scoping."""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Apply is_active filter if requested
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(is_active=False)
        
        # System admins see all stores
        if user.is_system_admin():
            return queryset
        
        # Non-admin users only see stores from their brand
        user_brand = user.get_brand()
        if user_brand:
            return queryset.filter(brand=user_brand)
        
        # Users without brand see nothing
        return queryset.none()
    
    def create(self, request, *args, **kwargs):
        """Handle store creation with proper permissions."""
        user = request.user
        
        # Only BRAND_MANAGER and SYSTEM_ADMIN can create stores
        if not user.has_role(SYSTEM_ADMIN, BRAND_MANAGER):
            return Response(
                {"detail": "forbidden", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # For BRAND_MANAGER, ensure they're creating store in their brand
        if not user.is_system_admin():
            brand_id = request.data.get('brand')
            user_brand = user.get_brand()
            
            if not user_brand or str(user_brand.id) != str(brand_id):
                return Response(
                    {"detail": "forbidden", "code": "PERMISSION_DENIED"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Handle store updates with proper permissions."""
        user = request.user
        
        # STAFF cannot update stores
        if user.has_role(STAFF):
            return Response(
                {"detail": "forbidden", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Handle store deletion with proper permissions."""
        user = request.user
        
        # Only BRAND_MANAGER and SYSTEM_ADMIN can delete stores
        if not user.has_role(SYSTEM_ADMIN, BRAND_MANAGER):
            return Response(
                {"detail": "forbidden", "code": "PERMISSION_DENIED"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
