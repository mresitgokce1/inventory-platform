# Inventory Platform (Multi-Brand Stock & Order Management)

This repository hosts a multi-brand (Brand → Store → Warehouse/Shelf) inventory & order management system.

## Domain Overview

The platform is built around a multi-brand architecture with the following core entities:

### Brand
- **Purpose**: Top-level business entity that owns stores, categories, and products
- **Key Features**: 
  - Unique case-insensitive names
  - Active/inactive status
  - UUID-based identification
- **Access Control**: Only SYSTEM_ADMIN can create/modify brands

### Store
- **Purpose**: Physical retail locations belonging to a brand
- **Key Features**:
  - Unique names and codes per brand (case-insensitive)
  - Brand association (foreign key)
  - Active/inactive status
- **Access Control**: BRAND_MANAGER can create/manage stores within their brand

### Category
- **Purpose**: Hierarchical organization of products within a brand
- **Key Features**:
  - Parent-child relationships for hierarchical categories
  - Unique names per brand (case-insensitive)
  - Brand scoping ensures categories belong to specific brands
- **Access Control**: BRAND_MANAGER can create/manage categories within their brand

### Product
- **Purpose**: Items available for sale within the inventory system
- **Key Features**:
  - Unique SKUs per brand (case-insensitive)
  - Optional category association
  - Brand scoping with validation
  - Active/inactive status for inventory management
- **Access Control**: BRAND_MANAGER can create/manage products within their brand

## Role-Based Access Control

| Role | Brand | Store | Category | Product | Description |
|------|-------|-------|----------|---------|-------------|
| **SYSTEM_ADMIN** | Full CRUD | Full CRUD | Full CRUD | Full CRUD | Complete access across all brands |
| **BRAND_MANAGER** | Read only (own brand) | Full CRUD (own brand) | Full CRUD (own brand) | Full CRUD (own brand) | Manage all aspects within assigned brand |
| **STORE_MANAGER** | Read only (own brand) | Update only (own stores) | Read only (own brand) | Read only (own brand) | Limited to store management and read-only access |
| **STAFF** | Read only (own brand) | Read only (own brand) | Read only (own brand) | Read only (own brand) | Read-only access within assigned brand |

### Brand Scoping
- Non-admin users are automatically scoped to their assigned brand
- All data queries are filtered to show only relevant brand data
- Cross-brand access attempts return 403 Forbidden
- SYSTEM_ADMIN users see data across all brands

## High-Level Vision
- Roles: SystemAdmin, BrandManager, StoreManager, Staff, Public (QR)
- Products with multilingual (TR/EN) names, QR codes, price history (keep last 5)
- Stock layering: Product (store total) → Warehouse allocation → Shelf allocation
- Orders: NEW → ACCEPTED → DELIVERED → CANCELLED (no partial fulfillment MVP)
- Low stock: store global threshold + optional per-product override
- Tech: Django + DRF backend (API-first), React SPA frontend
- Auth: JWT (15m access, rotating refresh ~7d), strong password policy, rate limiting
- Soft delete & restore for users and products

## Getting Started

The backend Django skeleton is now set up with JWT authentication! Follow these steps to run the development server:

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# Run migrations
cd backend
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Run tests
pytest

# Check the health endpoint
curl http://127.0.0.1:8000/health/
```

## Authentication Usage Examples

The platform includes a robust JWT authentication system with role-based access control.

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "AdminPass123!"}'
```

Response:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "00d435c5-b7ce-46c7-aadb-e3252341764f",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "full_name": "Admin User",
    "role": "SYSTEM_ADMIN",
    "is_active": true,
    "is_staff": true,
    "created_at": "2025-09-04T07:05:42.877295Z",
    "updated_at": "2025-09-04T07:05:42.877325Z"
  }
}
```

### Access Protected Resources
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/users/me/
```

### Refresh Token (with Rotation)
```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

### Logout (Blacklist Token)
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

### List Users (Admin Only)
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/users/
```

## Domain API Usage Examples

### List Brands (Admin sees all, others see only their brand)
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/brands/
```

### Create a Brand (SYSTEM_ADMIN only)
```bash
curl -X POST http://localhost:8000/api/brands/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Brand",
    "is_active": true
  }'
```

### Create a Store (BRAND_MANAGER within their brand)
```bash
curl -X POST http://localhost:8000/api/stores/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "brand-uuid-here",
    "name": "Downtown Store",
    "code": "DT001",
    "is_active": true
  }'
```

### Create a Category with Parent
```bash
curl -X POST http://localhost:8000/api/categories/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "brand-uuid-here",
    "name": "Smartphones",
    "parent": "parent-category-uuid-here"
  }'
```

### Create a Product
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "brand-uuid-here",
    "sku": "PHONE001",
    "name": "iPhone 15",
    "category": "category-uuid-here",
    "is_active": true
  }'
```

### Filter Active Products
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  "http://localhost:8000/api/products/?is_active=true"
```

## Authentication Features

- **Custom User Model**: UUID-based ID, email login, role-based access
- **Strong Password Policy**: Minimum 10 characters with uppercase, lowercase, digit, and symbol
- **JWT Token Management**: 
  - Access tokens expire in 15 minutes
  - Refresh tokens expire in 7 days with automatic rotation
  - Blacklisted tokens prevent reuse
- **Role-Based Access Control**: SYSTEM_ADMIN, BRAND_MANAGER, STORE_MANAGER, STAFF
- **Soft Delete**: Users can be soft-deleted and restored
- **Account Security**: Deleted users cannot authenticate

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Refresh access token (rotates refresh token)
- `POST /api/auth/logout/` - Logout and blacklist refresh token

### User Management
- `GET /api/users/me/` - Get current user profile
- `PUT /api/users/me/` - Update current user profile
- `GET /api/users/` - List all users (System Admin only)

### Domain Endpoints
- `GET|POST /api/brands/` - List/create brands
- `GET|PUT|PATCH|DELETE /api/brands/{id}/` - Retrieve/update/delete specific brand
- `GET|POST /api/stores/` - List/create stores
- `GET|PUT|PATCH|DELETE /api/stores/{id}/` - Retrieve/update/delete specific store
- `GET|POST /api/categories/` - List/create categories
- `GET|PUT|PATCH|DELETE /api/categories/{id}/` - Retrieve/update/delete specific category
- `GET|POST /api/products/` - List/create products
- `GET|PUT|PATCH|DELETE /api/products/{id}/` - Retrieve/update/delete specific product

### Query Parameters
- `?is_active=true|false` - Filter by active status (brands, stores, products)

## Deferred Features

The following features are documented for future implementation:

- **Inventory Tracking**: Stock levels, warehouse/shelf allocation, stock movements
- **Product Variants**: Size, color, and other attribute variations
- **Soft Delete Unification**: Consistent soft delete across all domain models
- **Advanced Search**: Full-text search, filtering, and sorting capabilities
- **Deep Category Optimization**: Performance optimization for deeply nested categories
- **Multilingual Support**: Product and category names in multiple languages
- **QR Code Generation**: Automatic QR code generation for products
- **Price History**: Track and maintain product pricing history
- **Order Management**: Complete order lifecycle management
- **Audit Logging**: Comprehensive audit trail for all operations

## Development Flow (Using Copilot Agents)
1. Review /prompts/PR1_backend_skeleton_prompt.md
2. Open GitHub → Copilot → Agents → Select repo → Paste PR1 prompt → Run
3. Merge PR1 after review
4. Run PR2 prompt (JWT + User model)
5. Subsequent prompts (Brands, Products, Inventory, Orders, Security) will follow

## Documentation
- See docs/context_master.md for confirmed architectural decisions
- See prompts/master_architecture_prompt_v3.md to regenerate architecture document

## PR Checklist
See PR_CHECKLIST.md

## License
MIT (see LICENSE)

---
**Implemented**: Custom User model, JWT authentication, role-based permissions, soft delete functionality, domain foundation (Brand, Store, Category, Product models), brand-scoped access control, REST API endpoints
