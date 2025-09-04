"""User role constants for the inventory platform."""

# User role choices
SYSTEM_ADMIN = "SYSTEM_ADMIN"
BRAND_MANAGER = "BRAND_MANAGER"
STORE_MANAGER = "STORE_MANAGER"
STAFF = "STAFF"

ROLE_CHOICES = [
    (SYSTEM_ADMIN, "System Administrator"),
    (BRAND_MANAGER, "Brand Manager"),
    (STORE_MANAGER, "Store Manager"),
    (STAFF, "Staff"),
]

# Helper functions
def get_role_display(role):
    """Get display name for a role."""
    role_dict = dict(ROLE_CHOICES)
    return role_dict.get(role, role)


def is_admin_role(role):
    """Check if role is admin level."""
    return role == SYSTEM_ADMIN


def is_manager_role(role):
    """Check if role is manager level."""
    return role in [SYSTEM_ADMIN, BRAND_MANAGER, STORE_MANAGER]