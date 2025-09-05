# Inventory Management App

This Django app provides comprehensive inventory management functionality for the inventory platform.

## Features

- **Product-Store Inventory Tracking**: Track stock levels for each product at each store location
- **Stock Movement Recording**: Complete audit trail of all inventory changes
- **Multi-store Support**: Handle inventory across multiple store locations
- **Brand Scoping**: Enforce brand-level access control and data isolation
- **Role-based Permissions**: Different access levels based on user roles
- **Low Stock Alerts**: Identify products below minimum stock levels
- **Transfer Management**: Handle stock transfers between stores
- **RESTful API**: Full CRUD operations via REST API
- **Admin Interface**: Django admin integration for easy management

## Models

### ProductStore
- Represents inventory of a specific product at a specific store
- Tracks current stock, reserved quantities, and minimum levels
- Enforces brand consistency between product and store

### StockMovement
- Records all inventory movements (inbound, outbound, transfers, adjustments)
- Immutable audit trail of all changes
- Automatically updates ProductStore quantities
- Supports various movement types with appropriate validation

## API Endpoints

- `/api/product-stores/` - ProductStore CRUD operations
- `/api/product-stores/low_stock/` - Low stock alert endpoint
- `/api/stock-movements/` - StockMovement operations (create, read, delete)
- `/api/stock-movements/by_product/` - Filter movements by product
- `/api/stock-movements/by_store/` - Filter movements by store

## Permissions

The app uses the existing `BrandScopedPermission` system:

- **SYSTEM_ADMIN**: Full access across all brands
- **BRAND_MANAGER**: Full access within their brand
- **STORE_MANAGER**: Read/update access within their brand
- **STAFF**: Read-only access within their brand

## Usage Examples

### Create Product Inventory Record
```python
from apps.inventory.models import ProductStore
from apps.products.models import Product
from apps.stores.models import Store

product_store = ProductStore.objects.create(
    product=product,
    store=store,
    quantity_on_hand=100,
    minimum_stock_level=10
)
```

### Record Stock Movement
```python
from apps.inventory.models import StockMovement

# Inbound stock
movement = StockMovement.objects.create(
    product_store=product_store,
    movement_type=StockMovement.INBOUND,
    quantity=50,
    reference_number="PO001",
    created_by=user
)
```

### Check Low Stock
```python
from apps.inventory.models import ProductStore
from django.db.models import F

low_stock = ProductStore.objects.filter(
    quantity_on_hand__lt=F('minimum_stock_level')
)
```

## Testing

The app includes comprehensive tests covering:
- Model validation and business logic
- API endpoints and permissions
- Stock movement automation
- Brand scoping and access control

Run tests with: `python -m pytest apps/inventory/tests.py -v`

## Admin Interface

Django admin is configured for both models with:
- Optimized querysets with select_related
- Appropriate filtering and search capabilities
- Read-only fields for computed properties
- Immutable stock movements (no editing allowed)

## Dependencies

- Django 5.0.8+
- djangorestframework
- django-filter (for advanced filtering)
- Existing apps: accounts, brands, stores, products, common