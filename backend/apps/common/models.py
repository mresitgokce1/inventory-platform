"""Common models and base classes."""
import uuid
from django.db import models
from .mixins import TimestampMixin


class BaseModel(TimestampMixin):
    """Base model with UUID primary key and timestamp fields."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']