"""Product and Category admin configuration."""
from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    
    list_display = ['name', 'brand', 'parent', 'created_at']
    list_filter = ['brand', 'created_at']
    search_fields = ['name', 'brand__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('brand', 'name', 'parent')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if not request.user.is_system_admin():
            user_brand = request.user.get_brand()
            if user_brand:
                qs = qs.filter(brand=user_brand)
            else:
                qs = qs.none()
        return qs


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin interface for Product model."""
    
    list_display = ['name', 'sku', 'brand', 'category', 'is_active', 'created_at']
    list_filter = ['brand', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'sku', 'brand__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('brand', 'sku', 'name', 'category', 'is_active')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if not request.user.is_system_admin():
            user_brand = request.user.get_brand()
            if user_brand:
                qs = qs.filter(brand=user_brand)
            else:
                qs = qs.none()
        return qs
