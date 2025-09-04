(Use this prompt in Copilot ONLY if you want it to generate an architecture design document before coding.
If you just want to start coding, skip and go straight to PR1 prompt.)

"""
Role: Act as a senior software architect & Django + React integration expert. Design the initial high-level architecture & domain design for a multi-brand inventory & order management system.

Decided Requirements (Confirmed):
- Single database, logical multi-tenancy via brand_id.
- Roles: SystemAdmin, BrandManager, StoreManager, Staff, Public (anonymous QR).
- Global audit log (no brand/store filtering requirement, but design should still allow filtering).
- Scale: ~1000 concurrent users; up to 5000 products mid-term.
- QR burst target up to 1000 RPS (protective rate limiting).
- No warehouse floor entity; multiple Warehouse entities simulate areas/floors.
- Stock layering: store total → warehouse allocations → shelf allocations (sum invariants).
- Product can appear in multiple warehouses & shelves.
- Track stock movements (IN, OUT, ADJUST) with actor.
- Orders: NEW→ACCEPTED→DELIVERED→CANCELLED (no partial fulfillment, no reservations).
- Cancellation reason optional.
- QR shows full product detail (price, stock, meta).
- QR anonymous rate limit: 100/min/IP.
- Multi-currency: TRY, USD, EUR.
- Price history: keep last 5 records, prune older on insert.
- Soft delete (Products, Users) unlimited restore; deleted user login → custom message.
- Multilingual (TR & EN) via modeltranslation for product/category.
- Locale by browser Accept-Language.
- Password policy: ≥10 chars, upper, lower, digit, symbol.
- JWT: access 15m; rotating refresh ~7d; blacklist old refresh.
- Rate limiting categories (QR vs authenticated vs anonymous) to be listed.
- ORM: Django ORM only; start SQLite; plan PostgreSQL migration.
- Frontend: React SPA (API-first) + DRF backend.
- No product variants; no barcode/EAN initial.
- Low stock: store global threshold + optional product override.
- Efficient price & stock queries; placeholder for caching.

OUTPUT FORMAT (Numbered Sections):
1. Assumptions
2. Domain Model
3. Architecture Overview (ASCII + components)
4. Module / App Breakdown
5. RBAC Matrix (key actions)
6. API Surface Overview
7. Stock & Allocation Model
8. Order Lifecycle
9. Price Model & History Policy
10. Low Stock Threshold Logic
11. Soft Delete & Restore Strategy
12. Security & Auth Strategy
13. i18n & Localization Strategy
14. Performance & Indexing Hints
15. Logging & Audit Strategy
16. Testing Strategy (high-level)
17. Risks & Mitigations
18. Future Extensions
19. Next Iteration Actions
20. Summary

Constraints:
- Concise, technical English (short Turkish clarifications allowed)
- 5–12 bullets typical per section
- Mark flexible suggestions with [REVIEW]
- No further questions (all decisions fixed)

Final Command:
Generate this 1st refined iteration draft now.
"""
