"""Store models for the inventory platform."""
from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import BaseModel
from apps.brands.models import Brand


class Store(BaseModel):
    """Store model representing a physical store location."""
    
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='stores')
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=50, db_index=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'stores_store'
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'
        ordering = ['-created_at']
        unique_together = [
            ('brand', 'name'),
            ('brand', 'code')
        ]
    
    def __str__(self):
        return f"{self.brand.name} - {self.name}"
    
    def clean(self):
        """Custom validation for store fields."""
        super().clean()
        if self.brand_id:
            # Check name uniqueness per brand (case-insensitive)
            name_exists = Store.objects.filter(
                brand=self.brand,
                name__iexact=self.name
            ).exclude(pk=self.pk).exists()
            
            if name_exists:
                raise ValidationError({'name': 'Store name must be unique within the brand (case-insensitive).'})
            
            # Check code uniqueness per brand (case-insensitive)
            code_exists = Store.objects.filter(
                brand=self.brand,
                code__iexact=self.code
            ).exclude(pk=self.pk).exists()
            
            if code_exists:
                raise ValidationError({'code': 'Store code must be unique within the brand (case-insensitive).'})
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
