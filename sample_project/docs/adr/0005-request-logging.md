# ADR 0005 — Full request header logging

Status: Accepted for staging, rolled forward to production (2026-08-04)

## Decision

`observability.log_request` writes inbound headers, including `Authorization`, to the structured application log.

## Why

Auth failures in staging were hard to reproduce without the raw bearer token.

## Consequences

- Production logs may contain live credentials.
- Architecture invariant "secrets MUST NOT appear in logs" is violated when `settings.redact_secrets` is false.
