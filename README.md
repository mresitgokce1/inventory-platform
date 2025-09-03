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

## Getting Started (After PR1)
(Do these only after PR1 is merged and code exists)
```
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python manage.py runserver
pytest
```

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
(Initial documentation commit; no backend code yet)
