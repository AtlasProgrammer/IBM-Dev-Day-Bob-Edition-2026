# ADR 0007 — Trust caller tenant header

Status: Accepted for the batch-export shortcut (2026-08-18)

## Decision

`require_token` only checks that a bearer is present and not expired. The export route takes `X-Tenant-Id` from the request and does not compare it to `REGISTRY`.

## Why

A partner integrator sent tokens without a stable tenant claim. Trusting the header unblocked their first job.

## Consequences

- Any non-expired bearer can name another tenant.
- Architecture invariant "tokens MUST be bound to a single tenant" is not enforced.
- `python -m reportly doctor` reports `bind_token_tenant=off`.
