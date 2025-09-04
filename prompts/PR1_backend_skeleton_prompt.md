# PR #1 – Backend Skeleton & Configuration (Copilot Agent Prompt)

(Directly paste this whole file content into Copilot Agents input to start PR1.)

Title: Backend skeleton & modular configuration

Context / Goal:
We need a clean Django backend foundation for a multi-brand inventory & order management platform. This PR only sets up structure, settings modularization, initial dependencies, and a basic health endpoint. No business models yet.

Architecture Decisions (reference):
- Python + Django + Django REST Framework (DRF)
- Single DB (start with SQLite), later PostgreSQL
- Apps to be created (empty or minimal): accounts, brands, stores, products, inventory, orders, pricing, audit, common
- React SPA will consume API later (not part of this PR)
- JWT auth, modeltranslation, etc. will come in later PRs

Scope (IN):
- Create Django project: core
- Modular settings: base.py, dev.py, test.py
- requirements.txt with pinned minimal dependencies
- Basic folder layout for future apps
- common.mixins module placeholder (SoftDelete + Timestamp placeholders as comments only)
- /health/ endpoint (returns JSON status)
- Basic README update: how to run backend dev server
- Makefile (optional) with common commands (run, test, lint)
- Pre-commit config (optional) with black + isort (placeholder)

Out of Scope (EXCLUDED):
- Any real models (User, Product, etc.)
- Auth / permissions
- Business logic, stock logic, price handling
- Migrations beyond the initial empty ones
- Frontend code

Acceptance Criteria:
- `python manage.py runserver` works using dev settings
- `GET /health/` returns: `{"status":"ok","env":"dev"}`
- Each target app directory exists with __init__.py
- requirements pinned (exact versions)
- README includes setup steps
- Basic pytest for /health/ passes

Tasks (Step-by-Step for Agent):
1. Add directory structure & empty __init__.py files.
2. Generate Django project "core".
3. Implement modular settings (base/dev/test).
4. INSTALLED_APPS with DRF + created apps.
5. Root URLConf + /health/ JSON view.
6. requirements.txt pinned:
   - Django ~= 5.0
   - djangorestframework ~= 3.15
   - PyYAML ~= 6.0
   - pytest ~= 8.2
   - pytest-django ~= 4.8
   - black ~= 24.4
   - isort ~= 5.13
7. Add test test_health.py (status 200 + JSON).
8. Update README run instructions.
9. Add .gitignore (Python + Node + env).
10. (Optional) Makefile for run/test/format.
11. Ensure formatting passes.

Non-Functional:
- English identifiers; minimal comments.
- No extra placeholder logic.

Output / Deliverables:
- All files above created/updated.
- Test passes.
- README updated.

CHANGELOG (append to PR description):
Added: skeleton, modular settings, health endpoint
Deferred: auth, domain models

Now generate the code changes according to this specification.
