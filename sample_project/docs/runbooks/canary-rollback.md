# Runbook — canary rollback on readiness 503

Symptom: deploy pipeline rolls back after `/health/ready` returns 503.

1. Check `logs/deploy-canary.log` for the first non-200 readiness probe.
2. If a migration is running, inspect `reportly/release/health.py`.
3. Online migrations MUST keep readiness at 200. Use `/health/live` plus a dedicated migration signal instead.
4. Re-run the canary only after readiness stays 200 for three consecutive probes.
