# Reportly

Sample production-shaped multi-tenant export platform used by ORCHESTRA.

Reportly routes authenticated export jobs through quotas, feature flags, audit, metrics, and webhooks. It ships online migrations plus canary health probes. Several architecture invariants are currently violated on purpose so the orchestrator has real incidents to close.

## Layout

- `reportly/api.py` — request routing and control-plane endpoints
- `reportly/auth.py` — bearer registry without tenant bind
- `reportly/tenants.py` / `quotas.py` / `flags.py` — tenancy and runtime gates
- `reportly/audit.py` / `metrics.py` / `webhooks.py` — side effects
- `reportly/export/` — export pipeline, including an abandoned streaming path
- `reportly/observability.py` — request logging
- `reportly/release/` — liveness, readiness, migrations, canary
- `docs/` — architecture, security, ADRs, onboarding, runbooks
- `incidents/` — active production tickets
- `logs/` — application, access, canary, and tenant-isolation traces
- `vcs/` — commit history and blame used by the Git Historian

## Known production pressure

| ID | Workflow | Symptom |
|---|---|---|
| BUG-1842 | Debugging / testing | 734 MB export dies with `MemoryError` |
| BUG-1901 | Code review / security | Bearer tokens land in logs |
| REL-2204 | Release / deployment | Canary rolls back on readiness 503 |
| TEN-2044 | Maintenance / security | Acme token exports Northwind data |

## Local commands

```bash
python -m reportly info
python -m reportly doctor
python -m reportly health
python -m reportly tenants
python -m reportly export
python -m unittest discover -s tests
```
