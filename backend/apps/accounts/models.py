import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils import timezone
from apps.common.mixins import TimestampMixin, SoftDeleteMixin
from .roles import ROLE_CHOICES, SYSTEM_ADMIN


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", SYSTEM_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def get_queryset(self):
        """Override to exclude soft-deleted users by default."""
        return super().get_queryset().filter(is_deleted=False)

    def unfiltered(self):
        """Return all users including soft-deleted."""
        return super().get_queryset()


class User(AbstractBaseUser, PermissionsMixin, TimestampMixin, SoftDeleteMixin):
    """Custom user model with email authentication and role-based access."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="STAFF")
    brand = models.ForeignKey('brands.Brand', on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def has_role(self, *roles):
        """Check if user has any of the specified roles."""
        return self.role in roles

    def is_system_admin(self):
        """Check if user is a system administrator."""
        return self.role == SYSTEM_ADMIN
    
    def get_brand(self):
        """Get the user's brand. SYSTEM_ADMIN users have no brand restriction."""
        if self.is_system_admin():
            return None
        return self.brand
