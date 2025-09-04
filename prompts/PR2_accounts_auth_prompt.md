# PR #2 – Accounts, User Model, Roles, Basic JWT Auth (Copilot Agent Prompt)

Title: User model, roles enum, JWT authentication endpoints, soft delete foundation

Context:
We now have the backend skeleton. Next step: implement custom User model with role handling and basic authentication endpoints using JWT (access 15m, rotating refresh ~7d). We also add soft delete fields for Users and a simple permission decorator. No brand/store linkage yet.

Architecture Points Relevant:
- Roles: SYSTEM_ADMIN, BRAND_MANAGER, STORE_MANAGER, STAFF
- Soft delete: is_deleted + deleted_at
- Deleted user cannot authenticate → custom JSON
- Password policy (>=10 chars, upper, lower, digit, symbol)
- JWT rotation + blacklist old refresh

Scope (IN):
- Custom User model (email unique login)
- Fields: id (UUID), email, password(hash), first_name, last_name, role, is_active, is_superuser (only for system admin use), is_deleted, deleted_at, created_at, updated_at
- Role constants file
- Soft delete mixin usage
- Password validators module
- Auth endpoints:
  - POST /api/auth/login
  - POST /api/auth/refresh (rotates)
  - POST /api/auth/logout (blacklists current refresh)
- Block deleted user at login (ACCOUNT_DELETED message)
- require_roles decorator -> 403 {"detail":"forbidden","code":"PERMISSION_DENIED"}
- Endpoints:
  - GET /api/users/me
  - GET /api/users/ (SYSTEM_ADMIN only; simple list)
- Token settings: ACCESS=15m, REFRESH=7d, ROTATE_REFRESH_TOKENS=True
- Blacklist management (simplejwt blacklist app OR custom model)
- Tests (pytest):
  - Successful login
  - Deleted user login blocked
  - Refresh rotation creates new refresh, old invalid
  - require_roles decorator enforced
  - System admin can list users, staff cannot

Out of Scope:
- Brand/Store linking
- Password reset / email verification
- Restore user endpoint

Acceptance Criteria:
- AUTH_USER_MODEL set
- All tests pass
- README updated with auth curl example

Tasks:
1. Add role constants (accounts/roles.py).
2. Implement User model & manager.
3. Configure settings (AUTH_USER_MODEL, rest framework, simplejwt).
4. Add password validator.
5. Implement serializers & views (login/refresh/logout/me/list).
6. Implement blacklist/rotation.
7. require_roles decorator (common/permissions.py).
8. Tests (5).
9. README auth section update.

Non-Functional:
- Clean separation in accounts app.
- No leaking passwords; minimal logging.

CHANGELOG (append PR description):
Added: Custom User model, JWT auth, rotation, permissions decorator
Deferred: Brand linkage, restore user, password reset

Generate the code for this PR now.
