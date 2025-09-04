# Context Master (Architecture Decisions – v1)

Core Decisions:
- Single DB, logical multi-tenancy (brand_id).
- Roles: SYSTEM_ADMIN, BRAND_MANAGER, STORE_MANAGER, STAFF, Public (QR read-only).
- Products: QR code, multilingual (TR/EN), price history keep last 5.
- Stock layering: Product total_store_stock >= Σ warehouse allocations >= Σ shelf allocations.
- Orders: NEW→ACCEPTED→DELIVERED→CANCELLED; no partial fulfilment, no reservation.
- Low stock: store global threshold + optional per-product override.
- Authentication: JWT (15m access), rotating refresh (~7d), blacklist old refresh.
- Password policy: >=10 chars, upper, lower, digit, symbol.
- Soft delete: users & products (unlimited restore).
- Rate limits: (initial plan) QR public 100/min/IP; others to be detailed later.
- DB: start SQLite; plan future PostgreSQL migration.
- Frontend: React SPA; Backend: Django + DRF.
- i18n: django-modeltranslation for product/category fields.
- Currency: TRY, USD, EUR (multi-currency).
- Price pruning: upon new price insert, keep only latest 5 rows.
- Audit logging required (product, price change, order status, stock allocation).
- Security: RBAC decorator + brute force limit (to be implemented).
Pending (will evolve in docs produced by prompts):
- Exact index list
- Detailed entity schema
- OpenAPI draft
