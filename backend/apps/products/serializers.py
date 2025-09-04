"""Product and Category serializers for the inventory platform."""
from rest_framework import serializers
from .models import Category, Product
from apps.brands.serializers import BrandSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.IntegerField(source='children.count', read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'brand', 'brand_name', 'name', 'parent', 'parent_name', 
            'children_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate category data."""
        brand = attrs.get('brand')
        name = attrs.get('name')
        parent = attrs.get('parent')
        
        if brand and name:
            # Check name uniqueness per brand (case-insensitive)
            instance_pk = self.instance.pk if self.instance else None
            name_exists = Category.objects.filter(
                brand=brand,
                name__iexact=name
            ).exclude(pk=instance_pk).exists()
            
            if name_exists:
                raise serializers.ValidationError({
                    'name': 'Category name must be unique within the brand (case-insensitive).'
                })
        
        # Validate parent belongs to same brand
        if parent and brand and parent.brand != brand:
            raise serializers.ValidationError({
                'parent': 'Parent category must belong to the same brand.'
            })
        
        # Prevent circular references
        if parent and self.instance and parent.pk == self.instance.pk:
            raise serializers.ValidationError({
                'parent': 'Category cannot be its own parent.'
            })
        
        return attrs


class CategoryDetailSerializer(CategorySerializer):
    """Detailed serializer for Category model with brand and parent details."""
    
    brand = BrandSerializer(read_only=True)
    parent = CategorySerializer(read_only=True)
    children = CategorySerializer(many=True, read_only=True)
    
    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['children']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""
    
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'brand', 'brand_name', 'sku', 'name', 'category', 
            'category_name', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate product data."""
        brand = attrs.get('brand')
        sku = attrs.get('sku')
        category = attrs.get('category')
        
        if brand and sku:
            # Check SKU uniqueness per brand (case-insensitive)
            instance_pk = self.instance.pk if self.instance else None
            sku_exists = Product.objects.filter(
                brand=brand,
                sku__iexact=sku
            ).exclude(pk=instance_pk).exists()
            
            if sku_exists:
                raise serializers.ValidationError({
                    'sku': 'Product SKU must be unique within the brand (case-insensitive).'
                })
        
        # Validate category belongs to same brand
        if category and brand and category.brand != brand:
            raise serializers.ValidationError({
                'category': 'Category must belong to the same brand as the product.'
            })
        
        return attrs


class ProductDetailSerializer(ProductSerializer):
    """Detailed serializer for Product model with brand and category details."""
    
    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields