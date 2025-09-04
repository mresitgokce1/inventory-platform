"""Product and Category models for the inventory platform."""
from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import BaseModel
from apps.brands.models import Brand


class Category(BaseModel):
    """Category model for organizing products."""
    
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=255, db_index=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    class Meta:
        db_table = 'products_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['-created_at']
        unique_together = [('brand', 'name')]
    
    def __str__(self):
        if self.parent:
            return f"{self.brand.name} - {self.parent.name} > {self.name}"
        return f"{self.brand.name} - {self.name}"
    
    def clean(self):
        """Custom validation for category fields."""
        super().clean()
        if self.brand_id:
            # Check name uniqueness per brand (case-insensitive)
            name_exists = Category.objects.filter(
                brand=self.brand,
                name__iexact=self.name
            ).exclude(pk=self.pk).exists()
            
            if name_exists:
                raise ValidationError({'name': 'Category name must be unique within the brand (case-insensitive).'})
        
        # Prevent circular references in parent-child relationships
        if self.parent and self.pk:
            if self.parent == self:
                raise ValidationError({'parent': 'Category cannot be its own parent.'})
            
            # Check for circular reference (more complex check)
            parent = self.parent
            while parent:
                if parent.pk == self.pk:
                    raise ValidationError({'parent': 'Circular reference detected in category hierarchy.'})
                parent = parent.parent
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)


class Product(BaseModel):
    """Product model representing items in inventory."""
    
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=100, db_index=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'products_product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        unique_together = [('brand', 'sku')]
    
    def __str__(self):
        return f"{self.brand.name} - {self.name} ({self.sku})"
    
    def clean(self):
        """Custom validation for product fields."""
        super().clean()
        if self.brand_id:
            # Check SKU uniqueness per brand (case-insensitive)
            sku_exists = Product.objects.filter(
                brand=self.brand,
                sku__iexact=self.sku
            ).exclude(pk=self.pk).exists()
            
            if sku_exists:
                raise ValidationError({'sku': 'Product SKU must be unique within the brand (case-insensitive).'})
        
        # Validate category belongs to same brand
        if self.category and self.brand_id and self.category.brand_id != self.brand_id:
            raise ValidationError({'category': 'Category must belong to the same brand as the product.'})
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
