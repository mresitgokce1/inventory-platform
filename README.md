# Inventory Platform (Multi-Brand Stock & Order Management)

This repository will host a multi-brand (Brand → Store → Warehouse/Shelf) inventory & order management system.

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
Implemented: Custom User model, JWT authentication, role-based permissions, soft delete functionality
