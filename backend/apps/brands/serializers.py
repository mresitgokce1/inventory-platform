"""Brand serializers for the inventory platform."""
from rest_framework import serializers
from .models import Brand


class BrandSerializer(serializers.ModelSerializer):
    """Serializer for Brand model."""
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate brand name for uniqueness (case-insensitive)."""
        if value:
            # Check for case-insensitive duplicates
            instance_pk = self.instance.pk if self.instance else None
            existing = Brand.objects.filter(
                name__iexact=value
            ).exclude(pk=instance_pk).exists()
            
            if existing:
                raise serializers.ValidationError('Brand name must be unique (case-insensitive).')
        return value