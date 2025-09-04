from django.db import models


class TimestampMixin(models.Model):
    """Placeholder mixin for timestamp fields."""

    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Placeholder mixin for soft delete functionality."""

    # is_deleted = models.BooleanField(default=False)
    # deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
