"""Store admin configuration."""
from django.contrib import admin
from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    """Admin interface for Store model."""
    
    list_display = ['name', 'code', 'brand', 'is_active', 'created_at']
    list_filter = ['brand', 'is_active', 'created_at']
    search_fields = ['name', 'code', 'brand__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('brand', 'name', 'code', 'is_active')
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
