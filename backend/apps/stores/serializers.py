"""Store serializers for the inventory platform."""
from rest_framework import serializers
from .models import Store
from apps.brands.serializers import BrandSerializer


class StoreSerializer(serializers.ModelSerializer):
    """Serializer for Store model."""
    
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    class Meta:
        model = Store
        fields = ['id', 'brand', 'brand_name', 'name', 'code', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate store data."""
        brand = attrs.get('brand')
        name = attrs.get('name')
        code = attrs.get('code')
        
        if brand and name:
            # Check name uniqueness per brand (case-insensitive)
            instance_pk = self.instance.pk if self.instance else None
            name_exists = Store.objects.filter(
                brand=brand,
                name__iexact=name
            ).exclude(pk=instance_pk).exists()
            
            if name_exists:
                raise serializers.ValidationError({
                    'name': 'Store name must be unique within the brand (case-insensitive).'
                })
        
        if brand and code:
            # Check code uniqueness per brand (case-insensitive)
            instance_pk = self.instance.pk if self.instance else None
            code_exists = Store.objects.filter(
                brand=brand,
                code__iexact=code
            ).exclude(pk=instance_pk).exists()
            
            if code_exists:
                raise serializers.ValidationError({
                    'code': 'Store code must be unique within the brand (case-insensitive).'
                })
        
        return attrs


class StoreDetailSerializer(StoreSerializer):
    """Detailed serializer for Store model with brand details."""
    
    brand = BrandSerializer(read_only=True)
    
    class Meta(StoreSerializer.Meta):
        fields = StoreSerializer.Meta.fields