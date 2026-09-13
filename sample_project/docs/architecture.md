# Reportly Architecture

Reportly is a multi-tenant export platform: HTTP API, tenant registry, quotas, feature flags, audit, webhooks, and canary health.

```
Client → ReportlyAPI → Auth/Identity → Quota → ExportService → Formatter → Storage
                 ↘ Observability / Audit / Metrics / Webhooks
                 ↘ FeatureFlags
                 ↘ /health/live  /health/ready  /internal/drift
```

## Invariants

- Exports MUST use bounded memory regardless of report size.
- Large reports MUST be streamed in chunks.
- Failures MUST NOT leave partial output in object storage.
- Secrets MUST NOT appear in application logs.
- Tokens MUST be bound to a single tenant.
- Cross-tenant export MUST return HTTP 403.
- `/health/ready` MUST stay HTTP 200 during online schema migrations so canary traffic is not drained.
- `/health/live` reports process liveness only.
- Feature flags that contradict an invariant MUST appear on `/internal/drift` and `python -m reportly doctor`.

## Control plane

| Surface | Role |
|---|---|
| `reportly/tenants.py` | Tenant catalog, plan, region |
| `reportly/auth.py` | Bearer registry and tenant bind |
| `reportly/quotas.py` | Monthly byte windows |
| `reportly/flags.py` | Runtime gates vs architecture |
| `reportly/audit.py` | Export trail |
| `reportly/metrics.py` | In-process counters |
| `reportly/webhooks.py` | Usage fanout |
| `reportly/release/canary.py` | Probe + rollback |

## Typical report sizes

- Interactive exports: 2–5 MB
- Scheduled tenant exports: 200 MB – 1.5 GB
- Compliance archives: multi-gigabyte streams
