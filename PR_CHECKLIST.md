# PR Checklist

Before merging any PR ensure:

- [ ] Scope matches PR description (no unrelated changes)
- [ ] New dependencies justified & pinned
- [ ] Migrations present and minimal (if models added)
- [ ] Tests added/updated and passing (pytest)
- [ ] RBAC decorators applied to new protected endpoints
- [ ] No secrets committed (search for SECRET / KEY / PASSWORD)
- [ ] README or docs updated if behavior or setup changed
- [ ] Formatting (black/isort) passes
- [ ] No obvious N+1 queries in new list endpoints
- [ ] For price changes: pruning logic covered by test (if touched)
- [ ] For stock changes: invariant checks covered by test (if touched)
