# Engineer onboarding

Welcome to Reportly.

1. Read `docs/architecture.md` and `docs/security.md` before changing export, auth, flags, or health.
2. ADRs in `docs/adr/` explain why current shortcuts exist. Treat conflicts with architecture invariants as incidents.
3. Run the local contract:
   - `python -m reportly doctor`
   - `python -m reportly health`
   - `python -m reportly tenants`
   - `python -m unittest discover -s tests`
4. `doctor` MUST report zero drift before a change is mergeable. Drift means a flag or setting contradicts an invariant.
5. Production logs live in `logs/`. Deploy traces live in `logs/deploy-canary.log`. Tenant-isolation traces live in `logs/tenant-isolation.log`.
6. Never ship an export change without a large-file / bounded-memory test.
7. Never log credentials. Redact `Authorization`, `Cookie`, and API keys.
8. Tokens MUST be bound to a single tenant. `X-Tenant-Id` is a claim, not a source of truth.
9. Canary deploys fail closed if `/health/ready` leaves 200.
