# Runbook — cross-tenant export

Symptom: audit or `logs/tenant-isolation.log` shows `cross_tenant=true` or `tenant.assumed`.

1. Confirm the bearer in `reportly.auth.REGISTRY` and the `X-Tenant-Id` claim.
2. Inspect `reportly/auth.py` `require_token`. If it returns after the expiry check, tenant bind is missing.
3. Check ADR 0007 — trusting the caller header is the usual regression window.
4. Bind the token to `Identity.tenant_id`, reject mismatches with HTTP 403, and add a test that uses `acme-live` against tenant `northwind`.
