"""Brand models for the inventory platform."""
from django.db import models
from apps.common.models import BaseModel


class Brand(BaseModel):
    """Brand model representing a business entity."""
    
    name = models.CharField(max_length=255, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'brands_brand'
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to ensure case-insensitive uniqueness."""
        # Convert name to lowercase for case-insensitive comparison
        if self.name:
            # Check for case-insensitive duplicates
            existing = Brand.objects.filter(
                name__iexact=self.name
            ).exclude(pk=self.pk).exists()
            
            if existing:
                from django.core.exceptions import ValidationError
                raise ValidationError({'name': 'Brand name must be unique (case-insensitive).'})
        
        super().save(*args, **kwargs)
